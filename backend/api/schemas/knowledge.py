from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str = ""
    embedding_model: Optional[str] = None
    chunk_size: int = 500
    similarity_threshold: float = 0.7


class KnowledgeBaseResponse(BaseModel):
    kb_id: str
    name: str
    description: str
    embedding_model: str
    chunk_size: int
    similarity_threshold: float
    created_at: datetime
    document_count: int


class DocumentResponse(BaseModel):
    doc_id: str
    kb_id: str
    filename: str
    chunks_count: int
    imported_at: datetime


class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    similarity_threshold: Optional[float] = None


class SearchResult(BaseModel):
    content: str
    filename: str
    chunk_index: int
    score: float