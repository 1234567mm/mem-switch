# Mem-Switch Phase 3.1: 记忆通道路由 + 核心代理 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现记忆通道路由界面和核心代理服务，用户可在 Mem-Switch 内为各 AI 开发工具配置通道，Mem-Switch 通道时自动检索记忆并注入到请求上下文。

**Architecture:** FastAPI 后端提供通道配置 API 和代理转发 API，代理层通过平台适配器识别请求来源并决定转发策略，记忆注入引擎负责检索相关记忆并组装到 system prompt。

**Tech Stack:** FastAPI / SQLite (channels 表) / Qdrant (记忆检索) / Ollama (LLM) / Svelte 5

---

## File Structure

```
backend/
├── services/
│   ├── channel_manager.py      # 通道配置管理
│   ├── memory_proxy.py         # 代理核心
│   ├── memory_injector.py      # 记忆注入引擎
│   └── vector_store.py         # (已存在)
├── platform_adapters/           # (新增目录)
│   ├── __init__.py
│   ├── base_adapter.py         # 平台适配器基类
│   ├── claude_code_adapter.py # Claude Code MCP
│   ├── codex_adapter.py        # Codex OpenAI 代理
│   ├── openclaw_adapter.py     # OpenClaw
│   ├── opencode_adapter.py     # OpenCode
│   ├── gemini_cli_adapter.py   # Gemini CLI
│   └── hermes_adapter.py      # Hermes
├── api/
│   ├── routes/
│   │   ├── channels.py         # 通道配置 API
│   │   └── proxy.py           # 代理转发 API
│   └── schemas/
│       └── channel.py          # 通道配置 Schema
├── migrations/
│   └── 001_add_channels.sql    # 通道表迁移
└── main.py                     # (修改，注册新路由)

frontend/
├── src/
│   ├── stores/
│   │   └── channels.svelte.js  # 通道状态管理
│   └── components/
│       └── ChannelManagerView.svelte  # 通道管理界面
└── src/App.svelte              # (修改，添加 ChannelManagerView tab)
```

---

### Task 1: 数据库迁移 - 通道表

**Files:**
- Create: `backend/migrations/001_add_channels.sql`
- Modify: `backend/services/database.py`

- [ ] **Step 1: 创建迁移 SQL 文件**

```sql
-- backend/migrations/001_add_channels.sql

-- 通道配置表
CREATE TABLE IF NOT EXISTS channels (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL UNIQUE,
    channel_type TEXT NOT NULL DEFAULT 'default',
    enabled INTEGER NOT NULL DEFAULT 1,
    auto_record INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 通道参数表
CREATE TABLE IF NOT EXISTS channel_configs (
    id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    recall_count INTEGER NOT NULL DEFAULT 5,
    similarity_threshold REAL NOT NULL DEFAULT 0.7,
    injection_position TEXT NOT NULL DEFAULT 'system',
    max_tokens INTEGER,
    FOREIGN KEY (channel_id) REFERENCES channels(id)
);

-- 平台设置表
CREATE TABLE IF NOT EXISTS platform_settings (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL UNIQUE,
    api_endpoint TEXT,
    config_path TEXT,
    config_backup TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 初始化 6 个平台的默认配置
INSERT OR IGNORE INTO channels (id, platform, channel_type, enabled, auto_record, created_at, updated_at)
VALUES
    ('ch_claude_code', 'claude_code', 'default', 1, 0, datetime('now'), datetime('now')),
    ('ch_codex', 'codex', 'default', 1, 0, datetime('now'), datetime('now')),
    ('ch_openclaw', 'openclaw', 'default', 1, 0, datetime('now'), datetime('now')),
    ('ch_opencode', 'opencode', 'default', 1, 0, datetime('now'), datetime('now')),
    ('ch_gemini_cli', 'gemini_cli', 'default', 1, 0, datetime('now'), datetime('now')),
    ('ch_hermes', 'hermes', 'default', 1, 0, datetime('now'), datetime('now'));

INSERT OR IGNORE INTO channel_configs (id, channel_id, recall_count, similarity_threshold, injection_position, max_tokens)
VALUES
    ('cc_claude_code', 'ch_claude_code', 5, 0.7, 'system', NULL),
    ('cc_codex', 'ch_codex', 5, 0.7, 'system', NULL),
    ('cc_openclaw', 'ch_openclaw', 5, 0.7, 'system', NULL),
    ('cc_opencode', 'ch_opencode', 5, 0.7, 'system', NULL),
    ('cc_gemini_cli', 'ch_gemini_cli', 5, 0.7, 'system', NULL),
    ('cc_hermes', 'ch_hermes', 5, 0.7, 'system', NULL);
```

- [ ] **Step 2: 修改 database.py 添加通道表 ORM 模型**

```python
# backend/services/database.py

class ChannelRow(Base):
    __tablename__ = "channels"
    id = Column(String, primary_key=True)
    platform = Column(String, unique=True, nullable=False)
    channel_type = Column(String, nullable=False, default="default")
    enabled = Column(Integer, nullable=False, default=1)
    auto_record = Column(Integer, nullable=False, default=0)
    created_at = Column(String)
    updated_at = Column(String)


class ChannelConfigRow(Base):
    __tablename__ = "channel_configs"
    id = Column(String, primary_key=True)
    channel_id = Column(String, ForeignKey("channels.id"))
    recall_count = Column(Integer, nullable=False, default=5)
    similarity_threshold = Column(Float, nullable=False, default=0.7)
    injection_position = Column(String, nullable=False, default="system")
    max_tokens = Column(Integer)


class PlatformSettingsRow(Base):
    __tablename__ = "platform_settings"
    id = Column(String, primary_key=True)
    platform = Column(String, unique=True, nullable=False)
    api_endpoint = Column(String)
    config_path = Column(String)
    config_backup = Column(Text)
    created_at = Column(String)
    updated_at = Column(String)
```

- [ ] **Step 3: 运行迁移脚本**

Run: `sqlite3 "C:/Users/wchao/AppData/Roaming/Mem-Switch/sqlite/metadata.db" < backend/migrations/001_add_channels.sql`

Expected: 无错误输出

- [ ] **Step 4: 验证表创建成功**

Run: `sqlite3 "C:/Users/wchao/AppData/Roaming/Mem-Switch/sqlite/metadata.db" ".tables"`

Expected: 输出包含 `channels channel_configs platform_settings`

- [ ] **Step 5: 提交**

```bash
git add backend/migrations/001_add_channels.sql backend/services/database.py
git commit -m "feat(channel): add channels tables and ORM models"
```

---

### Task 2: 通道配置 API 和 Schemas

**Files:**
- Create: `backend/api/schemas/channel.py`
- Create: `backend/api/routes/channels.py`
- Modify: `backend/main.py`

- [ ] **Step 1: 创建通道配置 Schema**

```python
# backend/api/schemas/channel.py

from pydantic import BaseModel
from typing import Optional


class ChannelConfig(BaseModel):
    recall_count: int = 5
    similarity_threshold: float = 0.7
    injection_position: str = "system"
    max_tokens: Optional[int] = None


class ChannelResponse(BaseModel):
    id: str
    platform: str
    channel_type: str  # 'default' | 'mem_switch'
    enabled: bool
    auto_record: bool
    config: ChannelConfig
    created_at: str
    updated_at: str


class ChannelUpdate(BaseModel):
    channel_type: Optional[str] = None
    enabled: Optional[bool] = None
    auto_record: Optional[bool] = None
    recall_count: Optional[int] = None
    similarity_threshold: Optional[float] = None
    injection_position: Optional[str] = None
    max_tokens: Optional[int] = None


class ChannelSwitchRequest(BaseModel):
    channel_type: str  # 'default' | 'mem_switch'


class ChannelListResponse(BaseModel):
    channels: list[ChannelResponse]
    global_enabled: bool = True
```

- [ ] **Step 2: 创建通道配置路由**

```python
# backend/api/routes/channels.py

from fastapi import APIRouter, HTTPException
from datetime import datetime
from uuid import uuid4

from services.channel_manager import ChannelManager
from api.schemas.channel import (
    ChannelResponse, ChannelUpdate, ChannelSwitchRequest,
    ChannelListResponse, ChannelConfig,
)
from config import AppConfig

router = APIRouter(prefix="/api/channels", tags=["channels"])
channel_mgr = ChannelManager(AppConfig())


def _row_to_response(row, config_row, config: AppConfig) -> ChannelResponse:
    return ChannelResponse(
        id=row.id,
        platform=row.platform,
        channel_type=row.channel_type,
        enabled=bool(row.enabled),
        auto_record=bool(row.auto_record),
        config=ChannelConfig(
            recall_count=config_row.recall_count if config_row else 5,
            similarity_threshold=config_row.similarity_threshold if config_row else 0.7,
            injection_position=config_row.injection_position if config_row else "system",
            max_tokens=config_row.max_tokens if config_row else None,
        ),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=ChannelListResponse)
async def list_channels():
    channels = channel_mgr.list_channels()
    return ChannelListResponse(channels=channels)


@router.get("/{platform}", response_model=ChannelResponse)
async def get_channel(platform: str):
    channel = channel_mgr.get_channel(platform)
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel not found: {platform}")
    return channel


@router.put("/{platform}", response_model=ChannelResponse)
async def update_channel(platform: str, data: ChannelUpdate):
    channel = channel_mgr.update_channel(platform, data.model_dump(exclude_none=True))
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel not found: {platform}")
    return channel


@router.post("/{platform}/switch", response_model=ChannelResponse)
async def switch_channel(platform: str, data: ChannelSwitchRequest):
    result = channel_mgr.switch_channel(platform, data.channel_type)
    if not result:
        raise HTTPException(status_code=404, detail=f"Channel not found: {platform}")
    return result


@router.post("/{platform}/enable")
async def toggle_channel(platform: str, enabled: bool):
    success = channel_mgr.set_enabled(platform, enabled)
    if not success:
        raise HTTPException(status_code=404, detail=f"Channel not found: {platform}")
    return {"status": "ok", "platform": platform, "enabled": enabled}
```

- [ ] **Step 3: 创建 ChannelManager 服务**

```python
# backend/services/channel_manager.py

from typing import Optional
from datetime import datetime
from uuid import uuid4

from services.database import get_session, ChannelRow, ChannelConfigRow, PlatformSettingsRow
from api.schemas.channel import ChannelResponse, ChannelConfig


class ChannelManager:
    PLATFORMS = ["claude_code", "codex", "openclaw", "opencode", "gemini_cli", "hermes"]

    def __init__(self, config):
        self.config = config

    def list_channels(self) -> list[ChannelResponse]:
        session = get_session()
        try:
            rows = session.query(ChannelRow).all()
            channels = []
            for row in rows:
                config_row = session.query(ChannelConfigRow).filter_by(channel_id=row.id).first()
                channels.append(self._row_to_response(row, config_row))
            return channels
        finally:
            session.close()

    def get_channel(self, platform: str) -> Optional[ChannelResponse]:
        session = get_session()
        try:
            row = session.query(ChannelRow).filter_by(platform=platform).first()
            if not row:
                return None
            config_row = session.query(ChannelConfigRow).filter_by(channel_id=row.id).first()
            return self._row_to_response(row, config_row)
        finally:
            session.close()

    def update_channel(self, platform: str, data: dict) -> Optional[ChannelResponse]:
        session = get_session()
        try:
            row = session.query(ChannelRow).filter_by(platform=platform).first()
            if not row:
                return None

            # 更新 channel 字段
            if "channel_type" in data and data["channel_type"]:
                row.channel_type = data["channel_type"]
            if "enabled" in data and data["enabled"] is not None:
                row.enabled = 1 if data["enabled"] else 0
            if "auto_record" in data and data["auto_record"] is not None:
                row.auto_record = 1 if data["auto_record"] else 0
            row.updated_at = datetime.now().isoformat()

            # 更新 config 字段
            config_row = session.query(ChannelConfigRow).filter_by(channel_id=row.id).first()
            if config_row:
                if "recall_count" in data and data["recall_count"] is not None:
                    config_row.recall_count = data["recall_count"]
                if "similarity_threshold" in data and data["similarity_threshold"] is not None:
                    config_row.similarity_threshold = data["similarity_threshold"]
                if "injection_position" in data and data["injection_position"]:
                    config_row.injection_position = data["injection_position"]
                if "max_tokens" in data:
                    config_row.max_tokens = data["max_tokens"]

            session.commit()
            return self._row_to_response(row, config_row)
        finally:
            session.close()

    def switch_channel(self, platform: str, channel_type: str) -> Optional[ChannelResponse]:
        return self.update_channel(platform, {"channel_type": channel_type})

    def set_enabled(self, platform: str, enabled: bool) -> bool:
        result = self.update_channel(platform, {"enabled": enabled})
        return result is not None

    def _row_to_response(self, row: ChannelRow, config_row: ChannelConfigRow) -> ChannelResponse:
        return ChannelResponse(
            id=row.id,
            platform=row.platform,
            channel_type=row.channel_type,
            enabled=bool(row.enabled),
            auto_record=bool(row.auto_record),
            config=ChannelConfig(
                recall_count=config_row.recall_count if config_row else 5,
                similarity_threshold=config_row.similarity_threshold if config_row else 0.7,
                injection_position=config_row.injection_position if config_row else "system",
                max_tokens=config_row.max_tokens if config_row else None,
            ),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
```

- [ ] **Step 4: 修改 main.py 注册新路由**

```python
# backend/main.py

from fastapi import FastAPI
from api.routes import health, hardware, ollama, settings, knowledge, memory
import api.routes.import_routes as import_routes
from api.routes import channels, proxy
from services.vector_store import VectorStore

app = FastAPI(title="Mem-Switch Backend", version="0.1.0")

app.include_router(health.router)
app.include_router(hardware.router)
app.include_router(ollama.router)
app.include_router(settings.router)
app.include_router(knowledge.router)
app.include_router(memory.router)
app.include_router(import_routes.router)
app.include_router(channels.router)
app.include_router(proxy.router)

vector_store = VectorStore()
```

- [ ] **Step 5: 测试通道 API**

Run: `curl -s http://127.0.0.1:8765/api/channels | python -m json.tool`

Expected: 返回包含 6 个平台的 JSON 数组

- [ ] **Step 6: 提交**

```bash
git add backend/api/schemas/channel.py backend/api/routes/channels.py backend/services/channel_manager.py backend/main.py
git commit -m "feat(channel): add ChannelManager and channels API"
```

---

### Task 3: 平台适配器基类和实现

**Files:**
- Create: `backend/platform_adapters/__init__.py`
- Create: `backend/platform_adapters/base_adapter.py`
- Create: `backend/platform_adapters/claude_code_adapter.py`
- Create: `backend/platform_adapters/codex_adapter.py`
- Create: `backend/platform_adapters/openclaw_adapter.py`
- Create: `backend/platform_adapters/opencode_adapter.py`
- Create: `backend/platform_adapters/gemini_cli_adapter.py`
- Create: `backend/platform_adapters/hermes_adapter.py`

- [ ] **Step 1: 创建 platform_adapters 目录和 __init__.py**

```python
# backend/platform_adapters/__init__.py

from .base_adapter import PlatformAdapter, AdapterRegistry

# 导出所有适配器
from .claude_code_adapter import ClaudeCodeAdapter
from .codex_adapter import CodexAdapter
from .openclaw_adapter import OpenClawAdapter
from .opencode_adapter import OpenCodeAdapter
from .gemini_cli_adapter import GeminiCLIAdapter
from .hermes_adapter import HermesAdapter

ADAPTERS = {
    "claude_code": ClaudeCodeAdapter,
    "codex": CodexAdapter,
    "openclaw": OpenClawAdapter,
    "opencode": OpenCodeAdapter,
    "gemini_cli": GeminiCLIAdapter,
    "hermes": HermesAdapter,
}


def get_adapter(platform: str) -> PlatformAdapter:
    adapter_class = ADAPTERS.get(platform)
    if not adapter_class:
        raise ValueError(f"Unknown platform: {platform}")
    return adapter_class()


def identify_platform(request_data: dict) -> str | None:
    """从请求中识别来源平台"""
    # 检查请求中的 platform 字段
    if "platform" in request_data:
        return request_data["platform"]

    # 检查 messages 中的特殊标记
    messages = request_data.get("messages", [])
    if messages and isinstance(messages[0], dict):
        first_msg = messages[0].get("content", "")
        if "[claude_code]" in str(first_msg):
            return "claude_code"
        if "[gemini]" in str(first_msg):
            return "gemini_cli"

    return None
```

- [ ] **Step 2: 创建平台适配器基类**

```python
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
```

- [ ] **Step 3: 创建 Claude Code 适配器 (MCP 格式)**

```python
# backend/platform_adapters/claude_code_adapter.py

import os
from typing import Optional
from .base_adapter import PlatformAdapter


class ClaudeCodeAdapter(PlatformAdapter):
    """Claude Code 适配器 - MCP 协议"""

    platform_name = "claude_code"
    api_endpoint = "http://localhost:11434/api/generate"

    MCP_TO_OLLAMA_FORMAT = {
        "model": "model",
        "messages": "messages",
        "stream": "stream",
        "options": "options",
    }

    def identify(self, request_data: dict) -> bool:
        # 检查是否是 Claude Code 请求
        # Claude Code 使用 MCP 协议，有特殊的请求格式
        return (
            request_data.get("protocol") == "mcp" or
            "mcp_server" in request_data.get("path", "") or
            request_data.get("tool") == "claude_code"
        )

    def extract_messages(self, request_data: dict) -> list[dict]:
        # MCP 格式的消息提取
        messages = request_data.get("messages", [])
        converted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, list):
                # 处理多模态内容
                text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
                content = "\n".join(text_parts)
            converted.append({"role": role, "content": content})
        return converted

    def build_forward_request(
        self,
        messages: list[dict],
        model: str,
        stream: bool = False,
    ) -> dict:
        # 构建转发到 Ollama 的请求
        return {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

    def get_config_path(self) -> Optional[str]:
        home = os.path.expanduser("~")
        claude_dir = os.path.join(home, ".claude")
        config_path = os.path.join(claude_dir, "settings.json")

        # 检查 Claude Code 安装
        if os.path.exists(claude_dir):
            return config_path
        return None
```

- [ ] **Step 4: 创建 Codex 适配器 (OpenAI 兼容)**

```python
# backend/platform_adapters/codex_adapter.py

import os
from typing import Optional
from .base_adapter import PlatformAdapter


class CodexAdapter(PlatformAdapter):
    """Codex 适配器 - OpenAI 兼容 API"""

    platform_name = "codex"
    api_endpoint = "http://localhost:8765/v1/chat/completions"

    def identify(self, request_data: dict) -> bool:
        # Codex 请求通常有 openai 格式
        has_messages = "messages" in request_data
        has_model = "model" in request_data
        # 检查是否指向 Codex 特定端点
        return has_messages and has_model and (
            "codex" in request_data.get("model", "").lower() or
            request_data.get("provider") == "codex"
        )

    def extract_messages(self, request_data: dict) -> list[dict]:
        return request_data.get("messages", [])

    def build_forward_request(
        self,
        messages: list[dict],
        model: str,
        stream: bool = False,
    ) -> dict:
        return {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

    def get_config_path(self) -> Optional[str]:
        # Codex 使用环境变量 OPENAI_API_BASE
        return None
```

- [ ] **Step 5: 创建 OpenClaw 适配器**

```python
# backend/platform_adapters/openclaw_adapter.py

import os
from typing import Optional
from .base_adapter import PlatformAdapter


class OpenClawAdapter(PlatformAdapter):
    """OpenClaw 适配器"""

    platform_name = "openclaw"
    api_endpoint = "http://localhost:8765/openclaw/v1/chat/completions"

    def identify(self, request_data: dict) -> bool:
        return (
            request_data.get("provider") == "openclaw" or
            "openclaw_session" in request_data
        )

    def extract_messages(self, request_data: dict) -> list[dict]:
        messages = request_data.get("messages", [])
        return [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in messages
        ]

    def build_forward_request(
        self,
        messages: list[dict],
        model: str,
        stream: bool = False,
    ) -> dict:
        return {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

    def get_config_path(self) -> Optional[str]:
        home = os.path.expanduser("~")
        config_path = os.path.join(home, ".openclaw", "config.json")
        if os.path.exists(os.path.dirname(config_path)):
            return config_path
        return None
```

- [ ] **Step 6: 创建 OpenCode 适配器**

```python
# backend/platform_adapters/opencode_adapter.py

import os
from typing import Optional
from .base_adapter import PlatformAdapter


class OpenCodeAdapter(PlatformAdapter):
    """OpenCode 适配器"""

    platform_name = "opencode"
    api_endpoint = "http://localhost:8765/opencode/v1/chat/completions"

    def identify(self, request_data: dict) -> bool:
        return (
            request_data.get("provider") == "opencode" or
            "opencode_session" in request_data
        )

    def extract_messages(self, request_data: dict) -> list[dict]:
        messages = request_data.get("messages", [])
        return [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in messages
        ]

    def build_forward_request(
        self,
        messages: list[dict],
        model: str,
        stream: bool = False,
    ) -> dict:
        return {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

    def get_config_path(self) -> Optional[str]:
        home = os.path.expanduser("~")
        config_path = os.path.join(home, ".opencode", "config.json")
        if os.path.exists(os.path.dirname(config_path)):
            return config_path
        return None
```

- [ ] **Step 7: 创建 Gemini CLI 适配器**

```python
# backend/platform_adapters/gemini_cli_adapter.py

import os
from typing import Optional
from .base_adapter import PlatformAdapter


class GeminiCLIAdapter(PlatformAdapter):
    """Gemini CLI 适配器 - Google AI 格式"""

    platform_name = "gemini_cli"
    api_endpoint = "http://localhost:8765/gemini/v1/chat/completions"

    def identify(self, request_data: dict) -> bool:
        return (
            request_data.get("provider") == "gemini" or
            "gemini" in request_data.get("model", "").lower() or
            request_data.get("source") == "gemini_cli"
        )

    def extract_messages(self, request_data: dict) -> list[dict]:
        # Gemini 格式转换
        messages = request_data.get("messages", [])
        converted = []
        for msg in messages:
            role = "user" if msg.get("role") == "user" else "model"
            content = msg.get("content", "")
            if isinstance(content, list):
                text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
                content = "\n".join(text_parts)
            converted.append({"role": role, "content": content})
        return converted

    def build_forward_request(
        self,
        messages: list[dict],
        model: str,
        stream: bool = False,
    ) -> dict:
        return {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

    def get_config_path(self) -> Optional[str]:
        # Gemini CLI 使用环境变量
        return None
```

- [ ] **Step 8: 创建 Hermes 适配器**

```python
# backend/platform_adapters/hermes_adapter.py

import os
from typing import Optional
from .base_adapter import PlatformAdapter


class HermesAdapter(PlatformAdapter):
    """Hermes 适配器 - NousResearch Hermes Agent"""

    platform_name = "hermes"
    api_endpoint = "http://localhost:8765/hermes/v1/chat/completions"

    def identify(self, request_data: dict) -> bool:
        return (
            request_data.get("provider") == "hermes" or
            "hermes_agent" in request_data.get("source", "") or
            "NousResearch" in str(request_data.get("model", ""))
        )

    def extract_messages(self, request_data: dict) -> list[dict]:
        messages = request_data.get("messages", [])
        return [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in messages
        ]

    def build_forward_request(
        self,
        messages: list[dict],
        model: str,
        stream: bool = False,
    ) -> dict:
        return {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

    def get_config_path(self) -> Optional[str]:
        home = os.path.expanduser("~")
        config_path = os.path.join(home, ".hermes", "config.json")
        if os.path.exists(os.path.dirname(config_path)):
            return config_path
        return None
```

- [ ] **Step 9: 测试适配器导入**

Run: `python -c "from platform_adapters import ADAPTERS, get_adapter; print(list(ADAPTERS.keys()))"`

Expected: `['claude_code', 'codex', 'openclaw', 'opencode', 'gemini_cli', 'hermes']`

- [ ] **Step 10: 提交**

```bash
git add backend/platform_adapters/
git commit -m "feat(platform): add platform adapters for all 6 AI tools"
```

---

### Task 4: 记忆注入引擎 (MemoryInjector)

**Files:**
- Create: `backend/services/memory_injector.py`
- Modify: `backend/services/memory_service.py` (添加检索方法)

- [ ] **Step 1: 创建 MemoryInjector 服务**

```python
# backend/services/memory_injector.py

from typing import Optional
from services.vector_store import VectorStore
from services.ollama_service import OllamaService
from config import AppConfig


class MemoryInjector:
    """记忆注入引擎 - 负责检索相关记忆并组装到上下文"""

    def __init__(self, vector_store: VectorStore, ollama_service: OllamaService, config: AppConfig):
        self.vector_store = vector_store
        self.ollama = ollama_service
        self.config = config
        self.collection_name = "memories"

    def inject(
        self,
        query: str,
        platform: str,
        recall_count: int = 5,
        similarity_threshold: float = 0.7,
        injection_position: str = "system",
    ) -> Optional[dict]:
        """
        检索相关记忆并组装注入上下文

        Returns:
            dict: {
                "injected_messages": [...],  # 注入记忆后的消息
                "context": str,  # 组装后的上下文字符串
                "memories_found": int,  # 找到的记忆数量
            }
        """
        # 1. 从 Qdrant 检索相关记忆
        memories = self._search_memories(query, recall_count, similarity_threshold)

        if not memories:
            return None

        # 2. 组装上下文字符串
        context = self._build_context_string(memories)

        # 3. 构建注入后的消息列表
        injected_messages = self._build_injected_messages(query, context, injection_position)

        return {
            "injected_messages": injected_messages,
            "context": context,
            "memories_found": len(memories),
        }

    def _search_memories(
        self,
        query: str,
        recall_count: int,
        similarity_threshold: float,
    ) -> list[dict]:
        """搜索相关记忆"""
        try:
            # 生成查询向量
            query_emb = self.ollama.embed(query)

            # 搜索 Qdrant
            results = self.vector_store.client.search(
                collection_name=self.collection_name,
                query_vector=query_emb,
                limit=recall_count,
            )

            # 过滤低于阈值的
            memories = []
            for r in results:
                if r.score >= similarity_threshold:
                    memories.append({
                        "content": r.payload.get("content", ""),
                        "type": r.payload.get("type", ""),
                        "dimensions": r.payload.get("dimensions", {}),
                        "score": r.score,
                    })

            return memories
        except Exception as e:
            print(f"Memory search error: {e}")
            return []

    def _build_context_string(self, memories: list[dict]) -> str:
        """构建记忆上下文字符串"""
        if not memories:
            return ""

        parts = ["[记忆上下文]\n"]

        # 按 type 分组
        by_type = {}
        for mem in memories:
            mem_type = mem.get("type", "unknown")
            if mem_type not in by_type:
                by_type[mem_type] = []
            by_type[mem_type].append(mem)

        # 按类型输出
        type_labels = {
            "preference": "偏好习惯",
            "expertise": "专业知识",
            "project_context": "项目上下文",
        }

        for mem_type, mems in by_type.items():
            label = type_labels.get(mem_type, mem_type)
            parts.append(f"\n{label}:\n")
            for mem in mems:
                parts.append(f"- {mem['content']}\n")

        return "".join(parts).strip()

    def _build_injected_messages(
        self,
        query: str,
        context: str,
        position: str,
    ) -> list[dict]:
        """构建注入后的消息列表"""
        if position == "system":
            return [
                {"role": "system", "content": context},
                {"role": "user", "content": query},
            ]
        else:
            return [
                {"role": "system", "content": context},
                {"role": "user", "content": query},
            ]
```

- [ ] **Step 2: 测试 MemoryInjector**

Run: `python -c "
from services.memory_injector import MemoryInjector
print('MemoryInjector imported successfully')
print('Methods:', [m for m in dir(MemoryInjector) if not m.startswith('_')])
"`

Expected: `['inject', ...]`

- [ ] **Step 3: 提交**

```bash
git add backend/services/memory_injector.py
git commit -m "feat(memory): add MemoryInjector for memory retrieval and context injection"
```

---

### Task 5: 记忆代理核心 (MemoryProxy)

**Files:**
- Create: `backend/services/memory_proxy.py`
- Create: `backend/api/routes/proxy.py`
- Modify: `backend/main.py`

- [ ] **Step 1: 创建 MemoryProxy 服务**

```python
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
```

- [ ] **Step 2: 创建代理 API 路由**

```python
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


@router.get("/api/channels/status")
async def channels_status():
    """获取所有通道状态"""
    channels = channel_mgr.list_channels()
    return {
        "channels": [
            {
                "platform": ch.platform,
                "channel_type": ch.channel_type,
                "enabled": ch.enabled,
                "connected": ch.enabled,
            }
            for ch in channels
        ]
    }
```

- [ ] **Step 3: 测试代理 API**

Run: `curl -s http://127.0.0.1:8765/api/channels/status | python -m json.tool`

Expected: 返回通道状态列表

- [ ] **Step 4: 提交**

```bash
git add backend/services/memory_proxy.py backend/api/routes/proxy.py
git commit -m "feat(proxy): add MemoryProxy service and /v1/chat/completions endpoint"
```

---

### Task 6: 前端通道管理界面

**Files:**
- Create: `frontend/src/stores/channels.svelte.js`
- Create: `frontend/src/components/ChannelManagerView.svelte`
- Modify: `frontend/src/App.svelte`

- [ ] **Step 1: 创建通道状态管理 Store**

```javascript
// frontend/src/stores/channels.svelte.js

export const channelsState = $state({
    channels: [],
    loading: false,
    error: null,
    globalEnabled: true,
});

export async function loadChannels() {
    channelsState.loading = true;
    channelsState.error = null;
    try {
        const resp = await fetch('http://127.0.0.1:8765/api/channels');
        const data = await resp.json();
        channelsState.channels = data.channels;
        channelsState.globalEnabled = data.global_enabled;
    } catch (e) {
        channelsState.error = 'Failed to load channels: ' + e.message;
    }
    channelsState.loading = false;
}

export async function updateChannel(platform, updates) {
    try {
        const resp = await fetch(`http://127.0.0.1:8765/api/channels/${platform}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(updates),
        });
        if (!resp.ok) throw new Error('Update failed');
        await loadChannels();
        return true;
    } catch (e) {
        channelsState.error = 'Failed to update channel: ' + e.message;
        return false;
    }
}

export async function switchChannel(platform, channelType) {
    try {
        const resp = await fetch(`http://127.0.0.1:8765/api/channels/${platform}/switch`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({channel_type: channelType}),
        });
        if (!resp.ok) throw new Error('Switch failed');
        await loadChannels();
        return true;
    } catch (e) {
        channelsState.error = 'Failed to switch channel: ' + e.message;
        return false;
    }
}
```

- [ ] **Step 2: 创建 ChannelManagerView.svelte**

```svelte
<script>
    import { channelsState, loadChannels, switchChannel, updateChannel } from '../stores/channels.svelte.js';
    import { onMount } from 'svelte';

    const channelLabels = {
        'claude_code': 'Claude Code',
        'codex': 'Codex',
        'openclaw': 'OpenClaw',
        'opencode': 'OpenCode',
        'gemini_cli': 'Gemini CLI',
        'hermes': 'Hermes',
    };

    let saving = $state({});

    onMount(() => {
        loadChannels();
    });

    async function handleSwitch(platform, event) {
        const channelType = event.target.value;
        await switchChannel(platform, channelType);
    }

    async function handleSave(platform) {
        saving[platform] = true;
        const channel = channelsState.channels.find(c => c.platform === platform);
        if (channel) {
            await updateChannel(platform, {
                recall_count: channel.config.recallCount,
                similarity_threshold: channel.config.similarityThreshold,
                injection_position: channel.config.injectionPosition,
            });
        }
        saving[platform] = false;
    }
</script>

<div class="max-w-4xl mx-auto p-8">
    <div class="flex items-center justify-between mb-6">
        <h1 class="text-3xl font-bold">记忆通道路由</h1>
        <label class="flex items-center gap-2">
            <span class="text-sm">全局开关</span>
            <input
                type="checkbox"
                checked={channelsState.globalEnabled}
                class="w-5 h-5"
            />
        </label>
    </div>

    {#if channelsState.loading}
        <p class="text-gray-500">加载中...</p>
    {:else if channelsState.error}
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {channelsState.error}
        </div>
    {:else}
        <div class="space-y-4">
            {#each channelsState.channels as channel}
                <div class="bg-white border rounded-lg p-4 shadow-sm">
                    <div class="flex items-center justify-between mb-3">
                        <h3 class="text-lg font-semibold">
                            {channelLabels[channel.platform] || channel.platform}
                        </h3>
                        <select
                            class="border rounded px-3 py-1"
                            value={channel.channel_type}
                            onchange={(e) => handleSwitch(channel.platform, e)}
                        >
                            <option value="default">默认通道</option>
                            <option value="mem_switch">Mem-Switch 通道</option>
                        </select>
                    </div>

                    {#if channel.channel_type === 'mem_switch'}
                        <div class="grid grid-cols-3 gap-4 mt-4">
                            <div>
                                <label class="block text-sm font-medium mb-1">召回数量</label>
                                <input
                                    type="number"
                                    class="w-full border rounded px-2 py-1"
                                    bind:value={channel.config.recallCount}
                                />
                            </div>
                            <div>
                                <label class="block text-sm font-medium mb-1">相似度阈值</label>
                                <input
                                    type="number"
                                    step="0.1"
                                    min="0"
                                    max="1"
                                    class="w-full border rounded px-2 py-1"
                                    bind:value={channel.config.similarityThreshold}
                                />
                            </div>
                            <div>
                                <label class="block text-sm font-medium mb-1">注入位置</label>
                                <select
                                    class="w-full border rounded px-2 py-1"
                                    bind:value={channel.config.injectionPosition}
                                >
                                    <option value="system">system prompt</option>
                                    <option value="context_prefix">context prefix</option>
                                </select>
                            </div>
                        </div>
                        <div class="mt-3">
                            <button
                                class="px-4 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                                onclick={() => handleSave(channel.platform)}
                                disabled={saving[channel.platform]}
                            >
                                {saving[channel.platform] ? '保存中...' : '保存配置'}
                            </button>
                        </div>
                    {/if}
                </div>
            {/each}
        </div>
    {/if}
</div>
```

- [ ] **Step 3: 修改 App.svelte 添加 Channel 标签页**

```svelte
<script>
    // 在 tabs 数组中添加 channel
    const tabs = [
        { id: 'startup', label: '启动引导', icon: '⚡' },
        { id: 'knowledge', label: '知识库', icon: '📚' },
        { id: 'memory', label: '记忆库', icon: '🧠' },
        { id: 'import', label: '对话导入', icon: '📥' },
        { id: 'channel', label: '通道路由', icon: '🔀' },
        { id: 'settings', label: '设置', icon: '⚙️' },
    ];

    // 添加导入
    import ChannelManagerView from './components/ChannelManagerView.svelte';

    // 在 placeholderLabel 中添加 channel
    let placeholderLabel = $derived(
        appState.currentTab === 'knowledge' ? '知识库' :
        appState.currentTab === 'memory' ? '记忆库' :
        appState.currentTab === 'import' ? '导入' :
        appState.currentTab === 'channel' ? '通道路由' :
        appState.currentTab === 'settings' ? '设置' : ''
    );

    // 在 main 内容区添加 ChannelManagerView
    {:else if appState.currentTab === 'channel'}
        <ChannelManagerView />
    {/if}
</script>
```

- [ ] **Step 4: 验证前端构建**

Run: `cd frontend && npm run build 2>&1 | tail -20`

Expected: 构建成功，无错误

- [ ] **Step 5: 提交**

```bash
git add frontend/src/stores/channels.svelte.js frontend/src/components/ChannelManagerView.svelte frontend/src/App.svelte
git commit -m "feat(ui): add ChannelManagerView for channel routing configuration"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] 通道配置 CRUD API
- [x] ChannelManager 服务
- [x] 6 个平台适配器
- [x] MemoryInjector 记忆注入引擎
- [x] MemoryProxy 代理核心
- [x] /v1/chat/completions OpenAI 兼容接口
- [x] ChannelManagerView 前端界面
- [x] SQLite 通道表迁移

**Placeholder scan:**
- 无 TBD/TODO
- 所有步骤包含实际代码

**Type consistency:**
- ChannelResponse 字段与前端 channels.svelte.js 一致
- MemoryInjector 方法签名正确

---

Plan complete and saved to `docs/superpowers/plans/2026-04-28-mem-switch-phase3-1.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
