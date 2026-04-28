# Mem-Switch Phase 3.1: 记忆通道路由 + 核心代理

> 日期: 2026-04-28
> 状态: 设计确认
> 依赖: Phase 2 已完成

---

## Context

Phase 2 完成了知识库、记忆库和对话导入服务。Phase 3.1 在此基础上实现**记忆通道路由**功能，让用户在 Mem-Switch 应用内为各 AI 开发工具独立配置通道，并实现**记忆代理核心**服务。

---

## 架构设计

### 整体架构

```
┌──────────────────────────────────────────────────────────────────┐
│  前端 UI (Svelte 5)                                               │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │ ChannelManager │  │ KnowledgeView  │  │  MemoryView    │     │
│  │    View       │  │               │  │               │     │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘     │
│          │                   │                   │               │
│          └───────────────────┼───────────────────┘               │
│                              │                                     │
│                    HTTP API (localhost:8765)                       │
└──────────────────────────────┼───────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────┐
│  FastAPI 后端                                                      │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  通道管理层                                                   │ │
│  │  - ChannelManager (通道配置 CRUD)                            │ │
│  │  - ChannelConfig 表 (SQLite)                                 │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                              │                                     │
│  ┌──────────────────────────▼──────────────────────────────────┐ │
│  │  记忆代理层                                                   │ │
│  │  - MemoryProxyService (请求路由/分发)                         │ │
│  │  - MemoryInjector (记忆检索/组装/注入)                        │ │
│  │  - PlatformAdapters (各平台适配器)                            │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                              │                                     │
│  ┌──────────────────────────▼──────────────────────────────────┐ │
│  │  外部 API 转发层                                              │ │
│  │  - /v1/chat/completions (OpenAI 兼容)                       │ │
│  │  - MCP Server (Claude Code)                                  │ │
│  │  - 各平台 API 端点                                           │ │
│  └──────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

### 数据流

**Mem-Switch 通道请求流程:**

```
1. AI 工具发送请求到 Mem-Switch 代理端口
      ↓
2. PlatformAdapter 识别来源工具
      ↓
3. ChannelManager 查询该工具的通道配置
      ↓
4a. 默认通道: 直接转发到原始 API
      ↓
4b. Mem-Switch 通道:
      ↓
   4b.1. MemoryInjector 从 Qdrant 检索相关记忆
      ↓
   4b.2. 按策略组装记忆上下文
      ↓
   4b.3. 注入到 system prompt
      ↓
   4b.4. 转发请求到 Ollama
      ↓
   4b.5. 返回响应给 AI 工具
```

---

## 数据库设计

### channels 表

```sql
CREATE TABLE channels (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL UNIQUE,  -- claude_code, codex, openclaw, opencode, gemini_cli, hermes
    channel_type TEXT NOT NULL DEFAULT 'default',  -- 'default' | 'mem_switch'
    enabled INTEGER NOT NULL DEFAULT 1,
    auto_record INTEGER NOT NULL DEFAULT 0,  -- 自动记录对话
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE channel_configs (
    id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    recall_count INTEGER NOT NULL DEFAULT 5,
    similarity_threshold REAL NOT NULL DEFAULT 0.7,
    injection_position TEXT NOT NULL DEFAULT 'system',  -- 'system' | 'context_prefix'
    max_tokens INTEGER,  -- NULL = 无限制
    FOREIGN KEY (channel_id) REFERENCES channels(id)
);

CREATE TABLE platform_settings (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL UNIQUE,
    api_endpoint TEXT,  -- 原始 API 端点
    config_path TEXT,   -- 配置文件路径
    config_backup TEXT,  -- 备份原始配置用于恢复
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

---

## API 设计

### 通道配置 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/channels` | 获取所有通道配置 |
| GET | `/api/channels/{platform}` | 获取指定平台通道配置 |
| PUT | `/api/channels/{platform}` | 更新指定平台通道配置 |
| POST | `/api/channels/{platform}/switch` | 切换通道类型 |
| POST | `/api/channels/{platform}/enable` | 启用/禁用通道 |

### 代理 API

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/v1/chat/completions` | OpenAI 兼容聊天完成接口 |
| POST | `/api/chat` | 通用聊天接口 (MCP 格式) |
| GET | `/api/channels/status` | 获取所有通道状态 |

### 请求/响应格式

**PUT /api/channels/{platform}**
```json
{
    "channel_type": "mem_switch",
    "enabled": true,
    "auto_record": true,
    "recall_count": 5,
    "similarity_threshold": 0.7,
    "injection_position": "system"
}
```

**POST /v1/chat/completions (Mem-Switch 代理请求)**
```json
{
    "model": "qwen2.5:7b",
    "messages": [
        {"role": "user", "content": "帮我写一个排序算法"}
    ],
    "stream": false
}
```

**Mem-Switch 通道响应 (注入记忆后)**
```json
{
    "model": "qwen2.5:7b",
    "messages": [
        {
            "role": "system",
            "content": "[记忆上下文] 偏好: 喜欢简洁代码; 专业知识: Python/Go; 项目: 开发 Mem-Switch 应用"
        },
        {"role": "user", "content": "帮我写一个排序算法"}
    ]
}
```

---

## 平台适配器设计

### BaseAdapter 接口

```python
class PlatformAdapter(ABC):
    """平台适配器基类"""

    platform_name: str  # 平台标识

    @abstractmethod
    def identify(self, request) -> str:
        """从请求中识别来源"""
        pass

    @abstractmethod
    def extract_messages(self, request) -> list[dict]:
        """提取消息列表"""
        pass

    @abstractmethod
    def build_request(self, messages: list[dict], injected_context: str = None) -> dict:
        """构建转发请求"""
        pass

    @abstractmethod
    def get_config_path(self) -> str | None:
        """获取配置文件路径"""
        pass

    @abstractmethod
    def get_api_endpoint(self) -> str:
        """获取 API 端点"""
        pass
```

### 各平台适配器

| 平台 | 适配方式 | API 端点 | 配置路径 |
|------|----------|----------|----------|
| Claude Code | MCP Server | `localhost:8765/mcp` | `~/.claude/settings.json` |
| Codex | OpenAI 兼容 | `localhost:8765/v1` | 环境变量 `OPENAI_API_BASE` |
| OpenClaw | REST API | `localhost:8765/openclaw/v1` | `~/.openclaw/config.json` |
| OpenCode | REST API | `localhost:8765/opencode/v1` | `~/.opencode/config.json` |
| Gemini CLI | Google AI 格式 | `localhost:8765/gemini/v1` | 环境变量 `GEMINI_API_BASE` |
| Hermes | REST API | `localhost:8765/hermes/v1` | `~/.hermes/config.json` |

---

## 前端组件

### ChannelManagerView.svelte

**布局:**
```
┌────────────────────────────────────────────────────────────────┐
│  记忆通道路由                                    [全局开关: ON] │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Claude Code      [Mem-Switch ▼]  [●] 自动记录对话        │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │  Codex           [默认通道 ▼]                             │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │  OpenClaw        [Mem-Switch ▼]  [○] 自动记录对话          │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │  OpenCode         [默认通道 ▼]                             │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │  Gemini CLI      [Mem-Switch ▼]  [●] 自动记录对话          │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │  Hermes          [默认通道 ▼]                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  注入策略配置                                              │ │
│  │                                                            │ │
│  │  召回数量: [5▼]  相似度阈值: [0.7▼]  注入位置: [system▼] │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                │
│  [保存配置]  [恢复原始设置]                                     │
└────────────────────────────────────────────────────────────────┘
```

**状态管理:**
- `channels.svelte.js` - 通道配置状态
- `channelConfig` - 各平台通道配置

---

## 组件清单

### 后端 (Phase 3.1 新增)

| 文件 | 描述 |
|------|------|
| `backend/services/channel_manager.py` | 通道配置管理服务 |
| `backend/services/memory_proxy.py` | 记忆代理核心服务 |
| `backend/services/memory_injector.py` | 记忆注入引擎 |
| `backend/platform_adapters/base_adapter.py` | 平台适配器基类 |
| `backend/platform_adapters/claude_code_adapter.py` | Claude Code MCP 适配器 |
| `backend/platform_adapters/codex_adapter.py` | Codex OpenAI 代理适配器 |
| `backend/platform_adapters/openclaw_adapter.py` | OpenClaw 适配器 |
| `backend/platform_adapters/opencode_adapter.py` | OpenCode 适配器 |
| `backend/platform_adapters/gemini_cli_adapter.py` | Gemini CLI 适配器 |
| `backend/platform_adapters/hermes_adapter.py` | Hermes 适配器 |
| `backend/api/routes/channels.py` | 通道配置 REST API |
| `backend/api/routes/proxy.py` | 代理转发 API |
| `backend/api/schemas/channel.py` | 通道配置 Schema |

### 前端 (Phase 3.1 新增)

| 文件 | 描述 |
|------|------|
| `frontend/src/stores/channels.svelte.js` | 通道状态管理 |
| `frontend/src/components/ChannelManagerView.svelte` | 通道配置界面 |

### 数据库迁移

| 文件 | 描述 |
|------|------|
| `backend/migrations/add_channels.sql` | 创建 channels, channel_configs, platform_settings 表 |

---

## 验证标准

1. **通道配置 CRUD**
   - [ ] GET /api/channels 返回所有平台配置
   - [ ] PUT /api/channels/{platform} 更新配置成功
   - [ ] 切换通道类型后，配置正确保存

2. **代理转发**
   - [ ] 默认通道: 请求直接转发到原始 API
   - [ ] Mem-Switch 通道: 检索记忆并注入到 system prompt

3. **记忆注入**
   - [ ] 从 Qdrant 检索相关记忆
   - [ ] 记忆正确组装到 system prompt
   - [ ] 注入位置配置生效

4. **平台适配**
   - [ ] Claude Code: MCP 格式正确处理
   - [ ] Codex: OpenAI 兼容接口正确转发
   - [ ] 其他平台适配器注册成功

5. **通道切换**
   - [ ] 配置文件正确备份
   - [ ] 切换后 AI 工具指向 Mem-Switch 代理
   - [ ] 卸载时正确恢复原始配置

---

## 实施顺序

1. **数据库迁移** - 创建 channels 相关表
2. **通道配置 API** - ChannelManager + channels routes
3. **前端通道管理界面** - ChannelManagerView
4. **平台适配器** - 各平台适配器实现
5. **记忆注入引擎** - MemoryInjector
6. **代理核心服务** - MemoryProxy + proxy routes
7. **端到端测试** - 全流程验证
