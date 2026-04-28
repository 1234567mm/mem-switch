from fastapi import APIRouter, HTTPException

from services.memory_service import MemoryService
from services.vector_store import VectorStore
from services.ollama_service import OllamaService
from config import AppConfig
from api.schemas.memory import MemoryResponse, SearchMemoriesRequest

router = APIRouter(prefix="/api/memory", tags=["memory"])
config = AppConfig()
vector_store = VectorStore()
ollama_svc = OllamaService(config)
memory_svc = MemoryService(vector_store, ollama_svc, config)


@router.get("/list", response_model=list[MemoryResponse])
async def list_memories(memory_type: str = None, limit: int = 100):
    memories = memory_svc.list_memories(memory_type=memory_type, limit=limit)
    return [
        MemoryResponse(
            memory_id=m.memory_id,
            type=m.type,
            content=m.content,
            dimensions=m.dimensions,
            confidence=m.confidence,
            source_session_id=m.source_session_id or "",
            created_at=m.created_at,
        )
        for m in memories
    ]


@router.post("/search", response_model=list[MemoryResponse])
async def search_memories(request: SearchMemoriesRequest):
    memories = memory_svc.search_memories(
        query=request.query,
        memory_type=request.memory_type,
        limit=request.limit,
    )
    return [
        MemoryResponse(
            memory_id=m.memory_id,
            type=m.type,
            content=m.content,
            dimensions=m.dimensions,
            confidence=m.confidence,
            source_session_id=m.source_session_id or "",
            created_at=m.created_at,
        )
        for m in memories
    ]


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    success = memory_svc.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete memory")
    return {"status": "deleted", "memory_id": memory_id}