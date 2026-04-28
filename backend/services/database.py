from sqlalchemy import create_engine, Column, String, Text, Float, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from config import SQLITE_DIR
from datetime import datetime

DB_PATH = SQLITE_DIR / "metadata.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ConfigRow(Base):
    __tablename__ = "config"
    key = Column(String, primary_key=True)
    value = Column(Text)


class SessionRow(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True)
    source = Column(String)
    import_time = Column(DateTime, default=datetime.now)
    deleted = Column(Boolean, default=False)


class MemoryRow(Base):
    __tablename__ = "memories"
    id = Column(String, primary_key=True)
    type = Column(String)
    content = Column(Text)
    confidence = Column(Float)
    qdrant_id = Column(String)
    source_session_id = Column(String)


class KnowledgeBaseRow(Base):
    __tablename__ = "knowledge_bases"
    kb_id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(Text)
    embedding_model = Column(String)
    chunk_size = Column(Integer)
    similarity_threshold = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    document_count = Column(Integer, default=0)


class DocumentRow(Base):
    __tablename__ = "documents"
    doc_id = Column(String, primary_key=True)
    kb_id = Column(String, ForeignKey("knowledge_bases.kb_id"))
    filename = Column(String)
    file_path = Column(String)
    chunks_count = Column(Integer)
    imported_at = Column(DateTime, default=datetime.now)


Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()
