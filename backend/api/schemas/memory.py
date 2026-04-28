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
