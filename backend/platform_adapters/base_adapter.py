# backend/platform_adapters/base_adapter.py

from abc import ABC, abstractmethod
from typing import Optional
import os
import json


class PlatformAdapter(ABC):
    """平台适配器基类"""

    platform_name: str = "base"
    api_endpoint: str = ""

    @abstractmethod
    def identify(self, request_data: dict) -> bool:
        """识别是否来自本平台"""
        pass

    @abstractmethod
    def extract_messages(self, request_data: dict) -> list[dict]:
        """提取消息列表"""
        pass

    @abstractmethod
    def build_forward_request(
        self,
        messages: list[dict],
        model: str,
        stream: bool = False,
    ) -> dict:
        """构建转发到 Ollama 的请求"""
        pass

    def inject_context(
        self,
        messages: list[dict],
        context: str,
        position: str = "system",
    ) -> list[dict]:
        """向消息列表注入上下文"""
        if position == "system":
            # 插入到 system message
            return [{"role": "system", "content": context}] + messages
        else:
            # 插入到最前面
            return [{"role": "system", "content": context}] + messages

    def get_config_path(self) -> Optional[str]:
        """获取平台配置文件路径"""
        home = os.path.expanduser("~")
        return None

    def get_api_endpoint(self) -> str:
        """获取平台 API 端点"""
        return self.api_endpoint

    def backup_config(self, config_path: str) -> Optional[str]:
        """备份配置文件"""
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return f.read()
        except Exception:
            pass
        return None

    def restore_config(self, config_path: str, backup: str) -> bool:
        """恢复配置文件"""
        try:
            with open(config_path, "w") as f:
                f.write(backup)
            return True
        except Exception:
            return False


class AdapterRegistry:
    """适配器注册表"""

    _adapters = {}

    @classmethod
    def register(cls, name: str, adapter_class: type):
        cls._adapters[name] = adapter_class

    @classmethod
    def get(cls, name: str) -> Optional[PlatformAdapter]:
        adapter_class = cls._adapters.get(name)
        if not adapter_class:
            return None
        return adapter_class()

    @classmethod
    def list_platforms(cls) -> list[str]:
        return list(cls._adapters.keys())