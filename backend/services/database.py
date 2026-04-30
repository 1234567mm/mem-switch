from sqlalchemy import create_engine, Column, String, Text, Float, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from config import SQLITE_DIR
from datetime import datetime
from dataclasses import dataclass

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
    call_count = Column(Integer, default=0)


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
    view_count = Column(Integer, default=0)


class ChannelRow(Base):
    __tablename__ = "channels"
    id = Column(String, primary_key=True)
    platform = Column(String, unique=True, nullable=False)
    channel_type = Column(String, nullable=False, default="default")
    enabled = Column(Integer, nullable=False, default=1)
    auto_record = Column(Integer, nullable=False, default=0)
    created_at = Column(String)
    updated_at = Column(String)


class ChannelConfigRow(Base):
    __tablename__ = "channel_configs"
    id = Column(String, primary_key=True)
    channel_id = Column(String, ForeignKey("channels.id"))
    recall_count = Column(Integer, nullable=False, default=5)
    similarity_threshold = Column(Float, nullable=False, default=0.7)
    injection_position = Column(String, nullable=False, default="system")
    max_tokens = Column(Integer)


class PlatformSettingsRow(Base):
    __tablename__ = "platform_settings"
    id = Column(String, primary_key=True)
    platform = Column(String, unique=True, nullable=False)
    api_endpoint = Column(String)
    config_path = Column(String)
    config_backup = Column(Text)
    created_at = Column(String)
    updated_at = Column(String)


@dataclass
class ImportTask:
    """ORM model for import_tasks table."""
    id: str
    source_type: str
    total_files: int
    completed_files: int
    failed_files: int
    skipped_files: int
    status: str
    progress: float
    created_at: str
    updated_at: str


class ImportTaskRow(Base):
    __tablename__ = "import_tasks"
    id = Column(String, primary_key=True)
    source_type = Column(String, nullable=False)
    total_files = Column(Integer)
    completed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    skipped_files = Column(Integer, default=0)
    status = Column(String, nullable=False)
    progress = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime)


@dataclass
class ImportTaskFile:
    """ORM model for import_task_files table."""
    id: int
    task_id: str
    file_name: str
    file_path: str
    status: str
    error: str
    memories_created: int
    session_id: str
    skipped: bool
    processed_at: str


class ImportTaskFileRow(Base):
    __tablename__ = "import_task_files"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, ForeignKey("import_tasks.id"))
    file_name = Column(String, nullable=False)
    file_path = Column(String)
    status = Column(String, nullable=False)  # success/failed/skipped
    error = Column(Text)
    memories_created = Column(Integer, default=0)
    session_id = Column(String)
    skipped = Column(Boolean, default=False)
    processed_at = Column(DateTime)


Base.metadata.create_all(engine)


def init_db():
    """Initialize database with additional tables not managed by ORM."""
    from config import SQLITE_DIR
    import sqlite3
    DB_PATH = SQLITE_DIR / "metadata.db"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_search_history_timestamp
        ON search_history(timestamp DESC)
    """)

    # Indexes for import tasks
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_import_tasks_created
        ON import_tasks(created_at DESC)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_import_task_files_task_id
        ON import_task_files(task_id)
    """)

    conn.commit()
    conn.close()


def get_session():
    return SessionLocal()
