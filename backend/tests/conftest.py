import pytest
import sys
from pathlib import Path
from uuid import uuid4
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.database import Base, MemoryRow, KnowledgeBaseRow, DocumentRow


# ── SQLite 临时库 ─────────────────────────────────────────────────

@pytest.fixture
def tmp_engine(tmp_path):
    """独立临时 SQLite，WAL 模式，与生产行为一致。"""
    db_path = tmp_path / f"test_{uuid4().hex}.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def tmp_session(tmp_engine):
    """与临时库绑定的 SQLAlchemy Session。"""
    Session = sessionmaker(bind=tmp_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def db_with_memories(tmp_session):
    """预填充 5 条 MemoryRow 记录。"""
    memory_ids = []
    for i in range(5):
        row = MemoryRow(
            id=str(uuid4()),
            type=["preference", "skill", "fact", "preference", "skill"][i],
            content=f"Test memory content {i}",
            confidence=0.8 + i * 0.02,
            qdrant_id=str(uuid4()),
            source_session_id="session_fixture",
            call_count=i,
        )
        tmp_session.add(row)
        memory_ids.append(row.id)
    tmp_session.commit()
    yield tmp_session, memory_ids


# ── ChromaDB Mock ────────────────────────────────────────────────

@pytest.fixture
def mock_chroma_collection():
    """模拟 ChromaDB collection。"""
    collection = MagicMock()
    collection._store = {}

    def fake_upsert(ids, documents=None, metadatas=None):
        for i, id_ in enumerate(ids):
            collection._store[id_] = {
                "document": documents[i] if documents else "",
                "metadata": metadatas[i] if metadatas else {},
            }
    collection.upsert.side_effect = fake_upsert

    collection.query.return_value = {
        "ids": [[]],
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }

    def fake_peek(limit=10):
        items = list(collection._store.items())[:limit]
        return {
            "ids": [k for k, _ in items],
            "documents": [v["document"] for _, v in items],
            "metadatas": [v["metadata"] for _, v in items],
        }
    collection.peek.side_effect = fake_peek

    def fake_delete(ids):
        for id_ in ids:
            collection._store.pop(id_, None)
    collection.delete.side_effect = fake_delete

    def fake_get():
        return {"ids": list(collection._store.keys())}
    collection.get.side_effect = fake_get

    collection.count.return_value = 0
    return collection


@pytest.fixture
def mock_vector_store(mock_chroma_collection):
    """模拟 VectorStore。"""
    vs = MagicMock()
    vs.client.get_collection.return_value = mock_chroma_collection
    vs.client.get_or_create_collection.return_value = mock_chroma_collection
    vs.scroll.return_value = ([], None)
    return vs


# ── Ollama Mock ─────────────────────────────────────────────────

@pytest.fixture
def mock_ollama():
    """返回固定 768 维向量。"""
    ollama = MagicMock()
    ollama.embed.return_value = [0.1] * 768
    return ollama


# ── AppConfig Mock ──────────────────────────────────────────────

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.get.return_value = "nomic-embed-text"
    config.embedding_model = "nomic-embed-text"
    return config
