# backend/api/routes/proxy.py

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import json

from services.memory_proxy import MemoryProxy
from services.channel_manager import ChannelManager
from services.memory_injector import MemoryInjector
from services.vector_store import VectorStore
from services.ollama_service import OllamaService
from config import AppConfig

router = APIRouter(tags=["proxy"])

# 初始化服务
config = AppConfig()
vector_store = VectorStore()
ollama_svc = OllamaService(config)
channel_mgr = ChannelManager(config)
memory_injector = MemoryInjector(vector_store, ollama_svc, config)
memory_proxy = MemoryProxy(channel_mgr, memory_injector, ollama_svc, config)


@router.api_route("/v1/chat/completions", methods=["POST"])
async def chat_completions(request: Request):
    """OpenAI 兼容的聊天完成接口"""
    try:
        request_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    result = await memory_proxy.handle_chat_completion(request_data)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return JSONResponse(content=result)


@router.api_route("/api/chat", methods=["POST"])
async def chat_api(request: Request):
    """通用聊天接口 (MCP 格式)"""
    try:
        request_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    result = await memory_proxy.handle_chat_completion(request_data)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return JSONResponse(content=result)