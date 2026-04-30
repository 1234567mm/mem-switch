import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from uuid import uuid4
from services.conversation_importer import ConversationImporter, ImportOptions
from adapters.base_adapter import Conversation


@pytest.fixture
def mock_vector_store():
    store = Mock()
    store.client = Mock()
    return store


@pytest.fixture
def mock_ollama():
    ollama = Mock()
    ollama.embed.return_value = [0.1] * 768
    return ollama


@pytest.fixture
def mock_config():
    config = Mock()
    config.ollama_host = "http://localhost:11434"
    config.embeddings_model = "nomic-embed-text"
    config.collection_name = "conversations"
    return config


@pytest.fixture
def importer(mock_vector_store, mock_ollama, mock_config):
    return ConversationImporter(mock_vector_store, mock_ollama, mock_config)


class TestImportOptions:
    def test_default_options(self):
        options = ImportOptions()
        assert options.extract_memories is True
        assert options.delete_after_import is False
        assert len(options.extract_dimensions) > 0

    def test_custom_options(self):
        options = ImportOptions(
            extract_memories=False,
            delete_after_import=True,
        )
        assert options.extract_memories is False
        assert options.delete_after_import is True


class TestConversationImporterInit:
    def test_init_creates_services(self, mock_vector_store, mock_ollama, mock_config):
        importer = ConversationImporter(mock_vector_store, mock_ollama, mock_config)
        assert importer.vector_store is mock_vector_store
        assert importer.ollama is mock_ollama
        assert importer.config is mock_config


class TestFormatConversationForEmbedding:
    def test_format_single_message(self, importer):
        conv = Conversation(
            session_id="test-1",
            source="test",
            timestamp=datetime.now(),
            messages=[{"role": "user", "content": "Hello"}],
        )
        result = importer.format_conversation_for_embedding(conv)
        assert "user: Hello" in result

    def test_format_multiple_messages(self, importer):
        conv = Conversation(
            session_id="test-1",
            source="test",
            timestamp=datetime.now(),
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
            ],
        )
        result = importer.format_conversation_for_embedding(conv)
        assert "user: Hello" in result
        assert "assistant: Hi there" in result

    def test_format_missing_role(self, importer):
        conv = Conversation(
            session_id="test-1",
            source="test",
            timestamp=datetime.now(),
            messages=[{"content": "Hello"}],
        )
        result = importer.format_conversation_for_embedding(conv)
        assert "unknown: Hello" in result

    def test_format_missing_content(self, importer):
        conv = Conversation(
            session_id="test-1",
            source="test",
            timestamp=datetime.now(),
            messages=[{"role": "user"}],
        )
        result = importer.format_conversation_for_embedding(conv)
        assert "user: " in result


class TestImportSingle:
    @patch("services.database.get_session")
    def test_import_single_success(self, mock_get_session, importer, mock_vector_store, mock_ollama):
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        conv = Conversation(
            session_id="test-123",
            source="test",
            timestamp=datetime.now(),
            messages=[{"role": "user", "content": "Hello"}],
        )
        options = ImportOptions(extract_memories=False)

        result = importer._import_single(conv, options)

        assert result["status"] == "success"
        assert result["session_id"] == "test-123"
        assert result["messages_count"] == 1

    @patch("services.database.get_session")
    def test_import_single_with_memory_extraction(self, mock_get_session, importer, mock_vector_store, mock_ollama):
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        mock_extractor = Mock()
        mock_extractor.extract_memories.return_value = {
            "decision": {"data": "Made a decision", "label": "Decision"}
        }
        importer.extractor = mock_extractor

        mock_memory_service = Mock()
        mock_memory_service.create_memory.return_value = {"id": "mem-1"}
        importer.memory_service = mock_memory_service

        conv = Conversation(
            session_id="test-456",
            source="test",
            timestamp=datetime.now(),
            messages=[{"role": "user", "content": "Let's decide something"}],
        )
        options = ImportOptions(extract_memories=True)

        result = importer._import_single(conv, options)

        assert result["status"] == "success"
        assert result["memories_created"] >= 0


class TestPreviewImport:
    def test_preview_import_not_found(self, importer):
        with patch("services.conversation_importer.get_adapter") as mock_get_adapter:
            mock_adapter = Mock()
            mock_adapter.detect.return_value = False
            mock_get_adapter.return_value = mock_adapter

            result = importer.preview_import("nonexistent")
            assert result == []

    def test_preview_import_found(self, importer):
        with patch("services.conversation_importer.get_adapter") as mock_get_adapter:
            mock_adapter = Mock()
            mock_adapter.detect.return_value = True
            mock_adapter.parse.return_value = [
                Conversation(
                    session_id="preview-1",
                    source="test",
                    timestamp=datetime.now(),
                    messages=[{"role": "user", "content": "Hello world test message"}],
                )
            ]
            mock_get_adapter.return_value = mock_adapter

            result = importer.preview_import("test")

            assert len(result) == 1
            assert result[0]["session_id"] == "preview-1"
            assert result[0]["message_count"] == 1


class TestDeleteSession:
    @patch("services.database.get_session")
    def test_delete_session_success(self, mock_get_session, importer, mock_vector_store):
        mock_session_db = Mock()
        mock_session_db.query.return_value.filter_by.return_value.first.return_value = Mock()
        mock_get_session.return_value = mock_session_db

        result = importer.delete_session("session-to-delete")

        assert result["status"] == "deleted"
        mock_vector_store.client.delete.assert_called_once()

    @patch("services.database.get_session")
    def test_delete_session_with_memories(self, mock_get_session, importer, mock_vector_store):
        mock_session_db = Mock()
        mock_row = Mock()
        mock_session_db.query.return_value.filter_by.return_value.first.return_value = mock_row
        mock_get_session.return_value = mock_session_db

        mock_memory_service = Mock()
        mock_memory_service.search_memories.return_value = [
            Mock(source_session_id="session-to-delete", memory_id="mem-1")
        ]
        importer.memory_service = mock_memory_service

        result = importer.delete_session("session-to-delete", delete_memories=True)

        assert result["status"] == "deleted"

    @patch("services.database.get_session")
    def test_delete_session_not_found(self, mock_get_session, importer, mock_vector_store):
        mock_session_db = Mock()
        mock_session_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_session.return_value = mock_session_db

        result = importer.delete_session("nonexistent-session")

        assert result["status"] == "deleted"
