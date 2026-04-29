# tests/conftest.py
import pytest
from unittest.mock import MagicMock, patch
import tempfile
import shutil

@pytest.fixture
def mock_vector_store():
    """Mock VectorStore for unit tests"""
    store = MagicMock()
    store.client = MagicMock()

    # Mock search 返回空结果
    class MockResult:
        score = 0.9
        payload = {"content": "test memory", "type": "preference"}
    store.client.search.return_value = [MockResult()]
    store.client.upsert.return_value = True

    return store

@pytest.fixture
def mock_ollama():
    """Mock OllamaService for unit tests"""
    ollama = MagicMock()
    ollama.embed.return_value = [0.1] * 768  # 768维 dummy embedding
    return ollama

@pytest.fixture
def temp_storage(tmp_path):
    """Temporary storage directory for tests"""
    storage = tmp_path / "test_storage"
    storage.mkdir()
    yield str(storage)
    shutil.rmtree(storage, ignore_errors=True)
