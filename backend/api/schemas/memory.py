from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MemoryResponse(BaseModel):
    memory_id: str
    type: str
    content: str
    dimensions: dict
    confidence: float
    source_session_id: str
    created_at: datetime


class SearchMemoriesRequest(BaseModel):
    query: str
    memory_type: str = None
    limit: int = 10


class MemoryUpdateRequest(BaseModel):
    content: str = None
    memory_type: str = None


class MemoryMergeRequest(BaseModel):
    memory_ids: list[str]
    merged_content: str = None
    merged_type: str = None
