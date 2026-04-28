# backend/services/memory_proxy.py

from typing import Optional
import httpx

from services.channel_manager import ChannelManager
from services.memory_injector import MemoryInjector
from services.vector_store import VectorStore
from services.ollama_service import OllamaService
from platform_adapters import get_adapter, identify_platform
from config import AppConfig


class MemoryProxy:
    """记忆代理核心服务"""

    def __init__(
        self,
        channel_manager: ChannelManager,
        memory_injector: MemoryInjector,
        ollama_service: OllamaService,
        config: AppConfig,
    ):
        self.channel_manager = channel_manager
        self.memory_injector = memory_injector
        self.ollama = ollama_service
        self.config = config
        self.ollama_host = config.get("ollama_host", "http://127.0.0.1:11434")

    async def handle_chat_completion(self, request_data: dict) -> dict:
        """
        处理聊天完成请求

        流程:
        1. 识别来源平台
        2. 查询通道配置
        3. 根据通道类型决定:
           - 默认通道: 直接转发
           - Mem-Switch 通道: 检索记忆 -> 注入 -> 转发
        """
        # 1. 识别平台
        platform = identify_platform(request_data) or request_data.get("platform", "unknown")

        # 2. 获取通道配置
        channel = self.channel_manager.get_channel(platform)
        if not channel:
            # 未知平台，默认放行
            return await self._forward_to_ollama(request_data)

        # 3. 检查是否启用
        if not channel.enabled:
            return await self._forward_to_ollama(request_data)

        # 4. 根据通道类型处理
        if channel.channel_type == "default":
            return await self._forward_to_ollama(request_data)
        else:
            return await self._handle_mem_switch_channel(request_data, channel, platform)

    async def _handle_mem_switch_channel(
        self,
        request_data: dict,
        channel,
        platform: str,
    ) -> dict:
        """处理 Mem-Switch 通道"""
        # 提取消息
        adapter = get_adapter(platform)
        messages = adapter.extract_messages(request_data)

        if not messages:
            return await self._forward_to_ollama(request_data)

        # 合并所有用户消息作为检索 query
        query = self._merge_user_messages(messages)

        # 检索记忆并注入
        injection = self.memory_injector.inject(
            query=query,
            platform=platform,
            recall_count=channel.config.recall_count,
            similarity_threshold=channel.config.similarity_threshold,
            injection_position=channel.config.injection_position,
        )

        if injection:
            # 使用注入后的消息
            forward_messages = injection["injected_messages"]
        else:
            # 无记忆，直接转发
            forward_messages = messages

        # 构建转发请求
        model = request_data.get("model", self.config.get("llm_model", "qwen2.5:7b"))
        stream = request_data.get("stream", False)

        forward_request = adapter.build_forward_request(
            messages=forward_messages,
            model=model,
            stream=stream,
        )

        # 转发到 Ollama
        return await self._forward_to_ollama(forward_request)

    async def _forward_to_ollama(self, request_data: dict) -> dict:
        """转发请求到 Ollama"""
        url = f"{self.ollama_host}/api/chat"

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, json=request_data)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"error": str(e), "status": 500}

    def _merge_user_messages(self, messages: list[dict]) -> str:
        """合并用户消息作为检索 query"""
        parts = []
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    parts.append(content)
        return " ".join(parts)