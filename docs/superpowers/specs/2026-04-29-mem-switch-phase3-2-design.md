# Mem-Switch Phase 3.2: 基础设施增强

> 日期: 2026-04-29
> 状态: 设计确认
> 依赖: Phase 3.1 已完成

---

## Context

Phase 3.1 完成了记忆通道路由和核心代理服务。Phase 3.2 进行基础设施增强,解决 Qdrant 锁问题、完善测试隔离、增强错误处理、为长时任务提供后台队列支持。

---

## 架构设计

### 整体架构

```
backend/
├── services/
│   ├── vector_store.py        # 修改: Chroma PersistentClient
│   ├── task_queue.py          # 新增: asyncio 后台任务队列
│   └── memory_service.py      # 修改: 支持异步任务
├── exceptions.py               # 新增: 自定义异常类
├── middleware/
│   └── logging.py            # 新增: 请求ID追踪 + 日志中间件
├── conftest.py                # 新增: pytest fixtures
├── migrations/
│   └── migrate_qdrant_to_chroma.py  # 新增: 数据迁移脚本
└── main.py                   # 修改: 注册中间件

tests/
└── conftest.py               # fixture: mock VectorStore, clean DB
```

### 关键设计决策

1. **Chroma 持久化**: `chromadb.PersistentClient(path=str(QDRANT_DIR))` - 数据迁移脚本从 Qdrant 导出 JSON → Chroma import
2. **任务队列**: Python `asyncio.Queue` + worker 任务,API 返回 `task_id` 供查询状态
3. **错误处理**: `MemSwitchError` 基类 + `VectorStoreError`,`OllamaConnectionError` 等子类
4. **日志中间件**: 生成 `X-Request-ID` header,结构化 JSON 日志输出

---

## 详细设计

### 1. Chroma 切换

**问题**: Qdrant portalocker bug 导致本地开发时锁冲突

**解决方案**: 切换到 Chroma 持久化模式

**VectorStore 接口保持不变**,仅内部实现从 Qdrant Client 改为 Chroma Client:

```python
# backend/services/vector_store.py

import chromadb
from chromadb.config import Settings

class VectorStore:
    def __init__(self):
        # 原有接口不变
        self.client = chromadb.PersistentClient(
            path=str(QDRANT_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        self._ensure_collections()
```

**数据迁移脚本**:

```python
# backend/migrations/migrate_qdrant_to_chroma.py

"""
从 Qdrant 迁移数据到 Chroma

使用方式:
    python -m migrations.migrate_qdrant_to_chroma

流程:
    1. 读取 Qdrant collection 中的所有 points
    2. 导出为 JSON
    3. 写入 Chroma collection
"""

import json
from pathlib import Path

def migrate_memories():
    # 读取 Qdrant 数据
    # 写入 Chroma
    pass
```

### 2. pytest Fixtures + Mock

**目标**: 测试隔离,开发者本地可同时跑多实例

**conftest.py**:

```python
# tests/conftest.py

import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_vector_store():
    """Mock VectorStore for unit tests"""
    store = MagicMock()
    store.client = MagicMock()
    store.client.search.return_value = []
    store.client.upsert.return_value = True
    return store

@pytest.fixture
def clean_test_db(tmp_path):
    """Clean test database for each test"""
    # 使用 tmp_path 创建临时数据库
    pass

@pytest.fixture
def mock_ollama():
    """Mock OllamaService for unit tests"""
    ollama = MagicMock()
    ollama.embed.return_value = [0.1] * 768  # dummy embedding
    return ollama
```

### 3. 自定义异常 + 日志中间件

**异常类层次**:

```python
# backend/exceptions.py

class MemSwitchError(Exception):
    """Base exception for Mem-Switch"""
    def __init__(self, message: str, request_id: str = None):
        self.message = message
        self.request_id = request_id
        super().__init__(self.message)

class VectorStoreError(MemSwitchError):
    """Vector store operation failed"""
    pass

class OllamaConnectionError(MemSwitchError):
    """Cannot connect to Ollama"""
    pass

class ChannelNotFoundError(MemSwitchError):
    """Channel configuration not found"""
    pass

class MemoryNotFoundError(MemSwitchError):
    """Memory not found"""
    pass
```

**日志中间件**:

```python
# backend/middleware/logging.py

import uuid
import logging
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("mem-switch")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # 结构化日志
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        }

        try:
            response = await call_next(request)
            log_data["status"] = response.status_code
            logger.info(json.dumps(log_data))
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as e:
            log_data["error"] = str(e)
            logger.error(json.dumps(log_data))
            raise
```

**main.py 注册**:

```python
# backend/main.py

from middleware.logging import LoggingMiddleware

app.add_middleware(LoggingMiddleware)
```

### 4. 后台任务队列

**设计**: Python `asyncio.Queue` + worker 任务

**用途**:
- 批量嵌入生成 (长时任务)
- 知识库文档处理
- 对话历史导入

**API 响应**:

```json
{
    "task_id": "uuid-string",
    "status": "queued|processing|completed|failed",
    "progress": 0.5,
    "result": null
}
```

**TaskQueue 服务**:

```python
# backend/services/task_queue.py

import asyncio
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Any

class TaskStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    task_id: str
    status: TaskStatus
    progress: float
    result: Any = None
    error: str = None

class TaskQueue:
    def __init__(self):
        self._queue = asyncio.Queue()
        self._tasks = {}
        self._worker = None

    async def enqueue(self, func: Callable, *args, **kwargs) -> str:
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = Task(
            task_id=task_id,
            status=TaskStatus.QUEUED,
            progress=0.0
        )
        await self._queue.put((task_id, func, args, kwargs))

        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(self._process_queue())

        return task_id

    async def get_task_status(self, task_id: str) -> Task:
        return self._tasks.get(task_id)

    async def _process_queue(self):
        while True:
            task_id, func, args, kwargs = await self._queue.get()
            self._tasks[task_id].status = TaskStatus.PROCESSING

            try:
                result = await func(*args, **kwargs)
                self._tasks[task_id].status = TaskStatus.COMPLETED
                self._tasks[task_id].result = result
                self._tasks[task_id].progress = 1.0
            except Exception as e:
                self._tasks[task_id].status = TaskStatus.FAILED
                self._tasks[task_id].error = str(e)

            self._queue.task_done()
```

**API 端点**:

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/tasks` | 提交任务,返回 task_id |
| GET | `/api/tasks/{task_id}` | 查询任务状态 |
| GET | `/api/tasks/{task_id}/result` | 获取任务结果 |

---

## 实施顺序

1. **Chroma 切换** - 改 VectorStore 实现 + 数据迁移脚本
2. **pytest fixtures** - 测试基础设施
3. **异常类 + 日志中间件** - 统一错误处理
4. **后台任务队列** - TaskQueue 服务 + API
5. **PWA** - 前端增强 (最后)

---

## 验证标准

1. **Chroma 切换**
   - [ ] VectorStore 接口不变,功能正常
   - [ ] 数据迁移脚本正确转换 Qdrant 数据到 Chroma
   - [ ] 本地多实例启动无锁冲突

2. **pytest fixtures**
   - [ ] `mock_vector_store` fixture 可用于单元测试
   - [ ] `clean_test_db` fixture 确保测试隔离

3. **异常 + 日志中间件**
   - [ ] 自定义异常类正确抛出和捕获
   - [ ] 所有请求携带 `X-Request-ID` header
   - [ ] 日志包含 request_id、method、path、status

4. **后台任务队列**
   - [ ] POST `/api/tasks` 返回 task_id
   - [ ] GET `/api/tasks/{task_id}` 返回正确状态
   - [ ] 长时任务不阻塞 API 响应

---

## 文件清单

| 文件 | 操作 | 描述 |
|------|------|------|
| `backend/services/vector_store.py` | 修改 | Chroma PersistentClient |
| `backend/migrations/migrate_qdrant_to_chroma.py` | 新增 | 数据迁移脚本 |
| `backend/exceptions.py` | 新增 | 自定义异常类 |
| `backend/middleware/logging.py` | 新增 | 日志中间件 |
| `backend/middleware/__init__.py` | 新增 | 中间件包 |
| `backend/services/task_queue.py` | 新增 | 任务队列服务 |
| `backend/api/routes/tasks.py` | 新增 | 任务 API 路由 |
| `backend/conftest.py` | 新增 | pytest fixtures |
| `backend/main.py` | 修改 | 注册中间件 |
| `tests/conftest.py` | 新增 | 测试 fixtures |

### PWA (Phase 3.2 后期)

| 文件 | 操作 | 描述 |
|------|------|------|
| `frontend/vite.config.js` | 修改 | PWA 插件配置 |
| `frontend/index.html` | 修改 | PWA manifest 链接 |
| `frontend/public/manifest.json` | 新增 | PWA manifest |
| `frontend/src/sw.js` | 新增 | Service Worker |
