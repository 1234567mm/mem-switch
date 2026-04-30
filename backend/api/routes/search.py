from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from services.search_service import SearchService

router = APIRouter(prefix="/api/search", tags=["search"])
search_service = SearchService()

class UnifiedSearchRequest(BaseModel):
    query: str
    scopes: list = ["memory", "knowledge"]
    limit: int = 20

    @field_validator("query")
    @classmethod
    def query_length(cls, v: str) -> str:
        if len(v) > 500:
            raise ValueError("query must be at most 500 characters")
        return v

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, v: list) -> list:
        valid_scopes = {"memory", "knowledge"}
        for scope in v:
            if scope not in valid_scopes:
                raise ValueError(f"scope must be one of {valid_scopes}")
        return v

    @field_validator("limit")
    @classmethod
    def limit_range(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("limit must be between 1 and 100")
        return v

@router.post("/unified")
async def unified_search(req: UnifiedSearchRequest):
    if not req.query.strip():
        return {"memory": {"items": [], "total": 0}, "knowledge": {"items": [], "total": 0}}
    try:
        results = search_service.unified_search(req.query, req.scopes, req.limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_history(limit: int = 10):
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    try:
        return {"history": search_service.get_search_history(limit)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hot")
async def get_hot(scope: str = "memory", limit: int = 5):
    valid_scopes = {"memory", "knowledge"}
    if scope not in valid_scopes:
        raise HTTPException(status_code=400, detail=f"scope must be one of {valid_scopes}")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    try:
        if scope == "memory":
            return {"items": search_service.get_hot_memories(limit)}
        elif scope == "knowledge":
            return {"items": search_service.get_hot_knowledge(limit)}
        return {"items": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
