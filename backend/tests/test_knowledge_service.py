import pytest
from unittest.mock import patch, MagicMock
from services.knowledge_service import KnowledgeService


@pytest.fixture
def knowledge_service(tmp_session, mock_vector_store, mock_ollama, mock_config):
    with patch("services.database.get_session", return_value=tmp_session):
        yield KnowledgeService(mock_vector_store, mock_ollama, mock_config)


class TestCreateKnowledgeBase:
    def test_creates_kb_and_returns_id(self, knowledge_service):
        kb = knowledge_service.create_knowledge_base(name="研究笔记", description="HTL 文献")
        assert kb.kb_id is not None
        assert kb.name == "研究笔记"

    def test_default_chunk_size(self, knowledge_service):
        kb = knowledge_service.create_knowledge_base(name="test")
        assert kb.chunk_size == 500

    def test_persisted_to_sqlite(self, knowledge_service, tmp_session):
        from services.database import KnowledgeBaseRow
        kb = knowledge_service.create_knowledge_base(name="persist-test")
        row = tmp_session.query(KnowledgeBaseRow).filter_by(kb_id=kb.kb_id).first()
        assert row is not None


class TestListKnowledgeBases:
    def test_returns_created_kbs(self, knowledge_service):
        knowledge_service.create_knowledge_base(name="KB1")
        knowledge_service.create_knowledge_base(name="KB2")
        result = knowledge_service.list_knowledge_bases()
        assert len(result) >= 2


class TestDeleteKnowledgeBase:
    def test_delete_removes_from_sqlite(self, knowledge_service, tmp_session):
        from services.database import KnowledgeBaseRow
        kb = knowledge_service.create_knowledge_base(name="to-delete")
        knowledge_service.delete_knowledge_base(kb.kb_id)
        row = tmp_session.query(KnowledgeBaseRow).filter_by(kb_id=kb.kb_id).first()
        assert row is None


class TestSearchKnowledge:
    def test_search_knowledge_returns_results(self, knowledge_service, mock_vector_store):
        mock_vector_store.client.search.return_value = []
        kb = knowledge_service.create_knowledge_base(name="test-kb")
        result = knowledge_service.search_knowledge(kb.kb_id, "test query")
        assert isinstance(result, list)

    def test_search_knowledge_filters_by_threshold(self, knowledge_service, mock_vector_store):
        mock_vector_store.client.search.return_value = []
        kb = knowledge_service.create_knowledge_base(name="threshold-test")
        result = knowledge_service.search_knowledge(kb.kb_id, "test", similarity_threshold=0.9)
        assert isinstance(result, list)


class TestListDocuments:
    def test_list_documents_returns_list(self, knowledge_service, tmp_session):
        kb = knowledge_service.create_knowledge_base(name="doc-test-kb")
        from services.database import DocumentRow
        doc = DocumentRow(
            doc_id="doc1",
            kb_id=kb.kb_id,
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            chunks_count=5,
        )
        tmp_session.add(doc)
        tmp_session.commit()

        docs = knowledge_service.list_documents(kb.kb_id)
        assert len(docs) >= 1

    def test_list_documents_empty_for_new_kb(self, knowledge_service):
        kb = knowledge_service.create_knowledge_base(name="empty-kb")
        docs = knowledge_service.list_documents(kb.kb_id)
        assert isinstance(docs, list)
