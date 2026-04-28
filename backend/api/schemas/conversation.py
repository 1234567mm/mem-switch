from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ConversationPreview(BaseModel):
    session_id: str
    source: str
    timestamp: str
    message_count: int
    preview: str


class ImportRequest(BaseModel):
    source_type: str
    source_path: Optional[str] = None
    extract_memories: bool = True
    extract_dimensions: list[str] = None


class ImportResult(BaseModel):
    status: str
    session_id: Optional[str] = None
    source: Optional[str] = None
    messages_count: int = 0
    memories_created: int = 0
    error: Optional[str] = None


class DeleteSessionRequest(BaseModel):
    session_id: str
    delete_memories: bool = False