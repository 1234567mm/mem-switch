from fastapi import APIRouter
from services.ollama_service import OllamaService
from config import AppConfig
from api.schemas.ollama import OllamaStatusResponse, ModelInfo, PullModelRequest, PullModelResponse

router = APIRouter(prefix="/api/ollama", tags=["ollama"])
_config = AppConfig()
_ollama_svc = OllamaService(_config.get("ollama_host", "http://127.0.0.1:11434"))


@router.get("/status", response_model=OllamaStatusResponse)
async def status():
    connected = _ollama_svc.is_connected()
    models = _ollama_svc.list_models() if connected else []
    return OllamaStatusResponse(connected=connected, models_count=len(models))


@router.get("/models", response_model=list[ModelInfo])
async def models():
    return [ModelInfo(**m) for m in _ollama_svc.list_models()]


@router.post("/pull", response_model=PullModelResponse)
async def pull(req: PullModelRequest):
    result = _ollama_svc.pull_model(req.model)
    return PullModelResponse(**result)
