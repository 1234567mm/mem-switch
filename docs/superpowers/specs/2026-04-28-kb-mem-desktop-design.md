# Mem-Switch Desktop 设计规格书

> 日期: 2026-04-28
> 状态: 设计确认，待实施规划
> 开发方案: 方案B - 记忆库+知识库并行，代理后置

---

## Context

用户希望开发一个跨平台桌面安装包应用，用于统一管理个人知识库和记忆库。核心需求：

- **安装包形式**: Linux、Windows、Mac均可安装使用（非CLI工具）
- **功能等权**: 知识库/记忆库/对话导入三者同等重要
- **自助对话导入**: 除claude-mem历史记录外，支持手动导入对话内容（JSON/Markdown/剪贴板），不绑定claude-mem
- **本地化部署**: 数据不上云，使用Ollama本地模型；架构预留云端接口，后期扩展
- **硬件自适应**: 启动时自动检测硬件配置，推荐合适模型
- **记忆提取可配置**: 用户自选提取维度（偏好习惯/专业知识/项目上下文）
- **统一向量库**: 对话和提取记忆存入同一向量库，高效低token消耗检索
- **按会话粒度**: 每个完整会话为一个向量单位，支持删除操作
- **记忆通道路由**: Mem-Switch应用内提供开关切换功能，用户控制各AI开发工具走默认通道还是Mem-Switch本地记忆通道（Phase 3）
- **主流开发平台适配**: Claude Code / Codex / OpenClaw / OpenCode / Gemini CLI / Hermes，记忆代理需适配各工具的对话格式和调用方式
- **README完整**: 详述对话导入→用户画像提取的实现流程

---

## 一、技术栈

| 组件 | 技术 | 理由 |
|------|------|------|
| 桌面框架 | Tauri v2 (Rust) | 安装包小、安全、性能优、v2支持侧边栏/多窗口 |
| 前端UI | Svelte 5 + TailwindCSS 4 | 轻量高效、 runes响应式、现代美观 |
| 后端服务 | Python FastAPI | 直接使用Mem0/Qdrant/Ollama生态 |
| 通信桥接 | HTTP API (localhost) | 前后端分离，易于维护 |
| 向量存储 | Qdrant (本地模式) | 高性能向量检索，支持本地嵌入模式 |
| 本地LLM | Ollama | 已部署，多模型适配不同硬件 |
| 元数据存储 | SQLite | 轻量、跨平台、无需额外服务 |

**硬件检测与模型推荐模块:**

```
启动流程:
1. 检测可用内存 / GPU显存 / CPU核心数
2. 匹配推荐模型列表:
   - <4GB RAM: qwen2.5-0.5b / tinyllama
   - 4-8GB RAM: qwen2.5-1.5b / mistral-7b-q4
   - 8-16GB RAM: qwen2.5-7b / llama3-8b
   - 16GB+ RAM / 有GPU: qwen2.5-14b / llama3-70b-q4
   - Embedding统一: nomic-embed-text (轻量高效)
3. 用户可覆盖推荐，手动选择模型
4. 首次启动自动下载推荐模型(用户确认)
```

---

## 二、应用架构

```
┌──────────────────────────────────────────────────────────┐
│  Tauri v2 桌面框架 (Rust)                                │
│  - 系统托盘、窗口管理、本地文件操作                       │
│  - 菜单栏、快捷键、原生通知                              │
│  - 硬件检测入口、应用生命周期管理                        │
└──────────────────────┬───────────────────────────────────┘
                       │ Tauri IPC
┌──────────────────────▼───────────────────────────────────┐
│  前端 UI (Svelte 5 + TailwindCSS 4)                     │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ 知识库   │ │ 记忆库   │ │ 对话导入 │ │ 设置     │    │
│  │ 管理     │ │ 管理     │ │ 界面     │ │ 界面     │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
│                                                          │
│  ┌──────────┐ ┌──────────┐                              │
│  │ 硬件检测 │ │ 记忆通道 │ (Phase 3)                    │
│  │ 引导页   │ │ 路由选择 │                              │
│  └──────────┘ └──────────┘                              │
└──────────────────────┬───────────────────────────────────┘
                       │ HTTP API (localhost:8765)
┌──────────────────────▼───────────────────────────────────┐
│  Python 后端服务 (FastAPI)                               │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  核心服务层                                        │  │
│  │  - KnowledgeService      (知识库/RAG)             │  │
│  │  - MemoryService          (记忆库/Mem0)            │  │
│  │  - ConversationImporter   (对话导入)              │  │
│  │  - ProfileManager         (用户画像)               │  │
│  │  - MemoryProxy            (记忆代理 - Phase 3)     │  │
│  │  - HardwareDetector       (硬件检测)               │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  数据层                                            │  │
│  │  - Qdrant (统一向量库: 对话+记忆+知识)             │  │
│  │  - SQLite (元数据/会话/用户画像)                   │  │
│  │  - Ollama (LLM推理 + Embedding)                    │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 三、核心功能模块

### 3.1 知识库管理界面

**功能:**
- 创建/删除知识库
- 导入文档（拖拽上传 PDF/DOCX/TXT/MD）
- 文档列表展示
- 知识检索界面（搜索框 + 结果列表）
- 知识库设置（切分策略、embedding模型、相似度阈值）

### 3.2 记忆库管理界面

**功能:**
- 记忆片段列表（时间轴展示）
- 用户画像编辑（可配置提取维度）
- 记忆检索界面
- 手动添加/删除记忆
- 提取维度配置：偏好习惯 / 专业知识 / 项目上下文（用户勾选）

### 3.3 对话导入界面（核心功能）

**支持的数据源:**

| 数据源 | 导入方式 | 格式 |
|--------|----------|------|
| claude-mem数据库 | 自动扫描 | SQLite DB |
| Claude Code历史 | 文件扫描 | JSONL |
| Codex历史 | 文件扫描 | OpenAI JSON |
| OpenClaw历史 | 文件扫描 | 自定义JSON |
| OpenCode历史 | 文件扫描 | Markdown/JSON混合 |
| Gemini CLI历史 | 文件扫描 | Google AI JSON |
| Hermes历史 | 文件扫描 | NousResearch Hermes Agent格式 |
| 手动JSON文件 | 文件上传 | JSON对话格式 |
| Markdown对话 | 文件上传 | .md格式 |
| 剪贴板粘贴 | 直接粘贴 | 纯文本 |
| 其他AI平台 | 文件上传 | 通用JSON |

**导入流程（README需详述）:**

```
1. 选择数据源 → 解析对话
2. 预览对话内容 → 用户确认
3. 选择提取维度（偏好习惯/专业知识/项目上下文）
4. Ollama提取关键信息 → 生成记忆片段
5. 对话+记忆存入统一向量库(Qdrant)
6. 更新用户画像(ProfileManager)
7. 显示导入统计结果
```

**关键特性:**
- 导入的会话支持删除操作
- 统一向量库：对话和提取记忆同一库，可独立或联合检索
- 按会话粒度：每个完整会话为一个向量单位

### 3.4 记忆通道路由（Phase 3）

**核心设计: 用户在Mem-Switch内控制通道切换**

Mem-Switch应用内提供记忆通道管理界面，用户为每个已安装的AI开发工具独立配置通道：

```
┌───────────────────────────────────────────────────────────┐
│ 记忆通道路由                                [全局开关]     │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  AI开发工具通道配置                                  │  │
│  │                                                     │  │
│  │  ● Claude Code      [Mem-Switch通道 ▼]  ● 自动记录对话  │  │
│  │  ● Codex            [默认通道 ▼]                    │  │
│  │  ● OpenClaw         [Mem-Switch通道 ▼]  ● 自动记录对话  │  │
│  │  ● OpenCode         [默认通道 ▼]                    │  │
│  │  ● Gemini CLI       [Mem-Switch通道 ▼]                 │  │
│  │  ● Hermes           [默认通道 ▼]                    │  │
│  │                                                     │  │
│  │  + 添加自定义工具...                                │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  通道说明:                                                │
│  默认通道: 工具直接调用原有LLM，不注入Mem-Switch记忆          │
│  Mem-Switch通道: 请求经Mem-Switch代理，自动注入相关记忆上下文     │
│                                                           │
│  记忆注入策略:                                            │
│  [召回数量: 5]  [相似度阈值: 0.7]  [注入位置: system prompt] │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

**主流开发平台适配:**

| 平台 | 对话格式 | 适配方式 | 配置要点 |
|------|----------|----------|----------|
| Claude Code | JSONL (项目会话) | 自动扫描 ~/.claude/projects/ | 记忆注入到system prompt |
| Codex | OpenAI兼容格式 | API代理模式 | 包装OpenAI API端点 |
| OpenClaw | 自定义JSON | 文件扫描+代理 | 扫描本地会话文件 |
| OpenCode | Markdown/JSON混合 | 文件扫描 | 检测工作目录会话 |
| Gemini CLI | Google AI格式 | API代理+文件扫描 | 包装Gemini API端点 |
| Hermes | 自定义协议 | 适配器模式 | https://github.com/NousResearch/hermes-agent.git |

**通道切换机制:**
- 用户在Mem-Switch界面为每个工具独立选择通道
- Mem-Switch代理作为本地中间层，监听各工具的API端口
- 切换Mem-Switch通道时，Mem-Switch自动配置工具指向代理端点
- 切换默认通道时，恢复工具原有API端点配置
- 全局开关：一键切换所有工具的通道模式

### 3.5 设置界面

- Ollama模型配置（硬件自适应推荐 + 手动覆盖）
- Qdrant连接设置
- 记忆提取维度配置
- 记忆库参数（过期时间、召回数量）
- 知识库参数（切分策略、相似度阈值）
- 数据存储路径设置
- 语言/主题设置

---

## 四、数据存储设计

### 4.1 统一向量库架构

```
Qdrant Collections:
├── conversations    # 原始对话（按会话粒度）
│   payload: {session_id, source, timestamp, messages, user_msg, assistant_msg}
│   向量: session级别embedding
│
├── memories         # 提取的记忆片段
│   payload: {memory_id, type, dimensions, source_session, confidence}
│   向量: 记忆内容embedding
│   type: preference | expertise | project_context
│
├── knowledge        # 知识库文档切片
│   payload: {kb_id, doc_id, chunk_index, content}
│   向量: 文档切片embedding
│
└── profiles         # 用户画像向量
    payload: {profile_id, dimensions, summary}
    向量: 画像摘要embedding
```

**检索策略:**
- 单库检索：用户指定搜索记忆/对话/知识
- 联合检索：跨库搜索，按相似度排序合并结果
- 对话引用记忆：记忆片段记录 source_session_id，可回溯原始对话

### 4.2 SQLite 元数据

```
Tables:
├── sessions         # 会话元数据（source, import_time, deleted标记）
├── memories         # 记忆元数据（type, dimensions, confidence, qdrant_id）
├── knowledge_bases  # 知识库配置
├── documents        # 文档元数据（kb_id, filename, chunks_count）
├── profiles         # 用户画像（维度配置, 更新时间）
├── import_records   # 导入记录（source_type, count, status）
└── config           # 应用配置
```

### 4.3 应用数据目录

```
Mem-Switch/                              # 跨平台统一位置
├── config.yaml                      # 应用配置
├── qdrant_storage/                  # Qdrant本地数据
├── sqlite/
│   ├── metadata.db                  # 元数据
│   └── conversations.db             # 会话记录
├── documents/                       # 原始文档副本
├── imports/                         # 导入的原始文件
└── logs/                            # 应用日志
```

---

## 五、对话导入模块详细设计

### 5.1 数据源适配器

```python
class ConversationImporter:
    ADAPTERS = {
        'claude_mem': ClaudeMemAdapter,
        'claude_code': ClaudeCodeAdapter,
        'codex': CodexAdapter,
        'openclaw': OpenClawAdapter,
        'opencode': OpenCodeAdapter,
        'gemini_cli': GeminiCLIAdapter,
        'hermes': HermesAdapter,
        'json_file': JSONFileAdapter,
        'markdown': MarkdownAdapter,
        'clipboard': ClipboardAdapter,
        'generic': GenericJSONAdapter,
    }

    def import_conversations(
        self,
        source_type: str,
        source_path: str = None,
        extract_dimensions: list[str] = None,  # 用户勾选的提取维度
        options: ImportOptions = None
    ) -> ImportResult:
        """
        流程:
        1. 检测/解析数据源
        2. 预览对话内容
        3. 用户确认导入选项 + 提取维度
        4. 会话级别embedding写入Qdrant conversations collection
        5. Ollama按维度提取关键信息(可选)
        6. 提取的记忆写入Qdrant memories collection
        7. 更新用户画像(ProfileManager)
        8. 写入SQLite元数据
        9. 返回导入统计
        """
```

### 5.2 会话删除支持

```python
def delete_session(self, session_id: str) -> DeleteResult:
    """
    删除会话流程:
    1. 从Qdrant conversations collection删除向量
    2. 查找该会话关联的记忆片段(memories collection)
    3. 用户选择: 同时删除关联记忆 / 保留记忆
    4. 从SQLite sessions表标记deleted
    5. 更新用户画像(如果受影响)
    """
```

### 5.3 记忆提取维度配置

```python
EXTRACT_DIMENSIONS = {
    'preference': {
        'label': '偏好习惯',
        'prompt': '提取用户语言风格、常用术语、交互偏好',
        'fields': ['language_style', 'terminology', 'interaction_pattern']
    },
    'expertise': {
        'label': '专业知识',
        'prompt': '提取用户领域方向、技能水平、学习轨迹',
        'fields': ['domain', 'skill_level', 'learning_path']
    },
    'project_context': {
        'label': '项目上下文',
        'prompt': '提取用户正在进行的工作、关注问题、解决方案',
        'fields': ['current_work', 'focus_issues', 'solutions']
    }
}
```

---

## 六、记忆代理与开发平台适配（Phase 3）

### 6.1 代理架构

```
┌──────────────────────────────────────────────────────────┐
│  Mem-Switch 记忆通道管理界面                                  │
│  - 用户为每个AI工具独立配置通道(默认/Mem-Switch)              │
│  - 全局开关一键切换                                       │
│  - 记忆注入策略配置(召回数量、相似度阈值)                  │
└──────────────────────┬───────────────────────────────────┘
                       │ 通道配置指令
┌──────────────────────▼───────────────────────────────────┐
│  Mem-Switch 代理服务 (localhost:8765)                         │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  工具适配层                                        │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐           │  │
│  │  │ClaudeCode│ │  Codex   │ │ OpenClaw │           │  │
│  │  │ 适配器   │ │  适配器  │ │  适配器  │           │  │
│  │  └──────────┘ └──────────┘ └──────────┘           │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐           │  │
│  │  │OpenCode  │ │Gemini CLI│ │  Hermes  │           │  │
│  │  │ 适配器   │ │  适配器  │ │  适配器  │           │  │
│  │  └──────────┘ └──────────┘ └──────────┘           │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  核心代理逻辑                                      │  │
│  │  1. 接收请求 → 识别来源工具                        │  │
│  │  2. 检查该工具通道配置(Mem-Switch界面中用户设置)        │  │
│  │  3. Mem-Switch通道: 检索记忆 → 注入上下文 → 转发请求   │  │
│  │  4. 默认通道: 直接转发请求，不注入记忆              │  │
│  │  5. 可选: 记录对话到Mem-Switch(用户勾选"自动记录")     │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  记忆注入引擎                                      │  │
│  │  - 检索相关记忆(Qdrant)                            │  │
│  │  - 按策略组装注入内容                              │  │
│  │  - 注入位置: system prompt / 上下文前缀             │  │
│  │  - 自动截断: 超过token限制时优先保留高相似度记忆    │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────┬───────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
   │ Ollama  │   │ Qdrant  │   │ SQLite  │
   │ (推理)  │   │ (检索)  │   │ (元数据)│
   └─────────┘   └─────────┘   └─────────┘
```

### 6.2 各平台适配详情

**Claude Code适配:**
- 自动扫描会话文件: `~/.claude/projects/*/conversations/`
- 代理方式: 修改Claude Code的MCP server配置，将Mem-Switch注册为MCP工具
- 记忆注入: 通过MCP tool_use方式在对话开始时注入记忆上下文
- 配置文件: `~/.claude/settings.json` 中添加Mem-Switch MCP server

**Codex适配:**
- 对话格式: OpenAI兼容API格式
- 代理方式: Mem-Switch作为本地OpenAI兼容API代理(localhost:8765/v1)
- 记忆注入: 在system prompt中注入记忆片段
- 配置: 设置OPENAI_API_BASE指向Mem-Switch代理端点

**OpenClaw适配:**
- 对话格式: 自定义JSON结构
- 代理方式: 文件扫描 + API适配
- 记忆注入: 读取配置文件注入上下文

**OpenCode适配:**
- 对话格式: Markdown/JSON混合
- 代理方式: 工作目录会话文件扫描
- 记忆注入: 编辑项目的记忆配置文件

**Gemini CLI适配:**
- 对话格式: Google AI格式
- 代理方式: Mem-Switch作为Gemini API代理
- 记忆注入: 在请求的systemInstruction字段注入记忆
- 配置: 设置GEMINI_API_BASE指向Mem-Switch代理端点

**Hermes适配:**
- 仓库: https://github.com/NousResearch/hermes-agent.git
- 对话格式: 需调研具体协议（基于仓库代码分析）
- 代理方式: 适配器模式，根据实际格式定制
- 首期先做基础文件扫描导入，代理模式后期完善

---

## 七、开发阶段（方案B）

### Phase 1: 基础框架搭建 (2周)

**目标:** Tauri窗口 + FastAPI后端 + 硬件检测引导

任务:
1. Tauri v2项目初始化 + Svelte 5前端
2. Python FastAPI后端服务搭建
3. Qdrant本地模式集成
4. 硬件检测模块 + 首次启动引导页
5. Ollama连接 + 模型推荐
6. 跨平台数据目录处理
7. IPC/HTTP通信桥接
8. 基础窗口/菜单UI

关键文件:
- `frontend/src/App.svelte`
- `frontend/src/components/StartupGuide.svelte`
- `backend/main.py`
- `backend/config.py`
- `backend/services/hardware_detector.py`
- `src-tauri/tauri.conf.json`

验证:
- 启动应用，硬件检测引导页正常显示
- Ollama连接成功，推荐模型下载
- Python后端API可访问 (localhost:8765/docs)

### Phase 2: 核心服务并行开发 (3周)

**目标:** 知识库 + 记忆库 + 对话导入，并行开发

**Agent B: 知识库服务**

任务:
1. KnowledgeService实现
2. 文档导入（PDF/DOCX/TXT/MD）
3. 文档切分 + embedding
4. 知识检索（单库/联合）
5. 知识库管理REST API

关键文件:
- `backend/services/knowledge_service.py`
- `backend/services/vector_store.py`
- `backend/api/routes/knowledge.py`

**Agent C: 记忆库 + 对话导入服务**

任务:
1. MemoryService实现（Mem0集成）
2. ProfileManager（用户画像 + 可配置维度）
3. 多数据源适配器实现
4. 对话导入流程（预览→提取→存储）
5. 会话删除功能
6. 记忆检索REST API

关键文件:
- `backend/services/memory_service.py`
- `backend/services/conversation_importer.py`
- `backend/services/profile_manager.py`
- `backend/adapters/*.py`

验证:
- 创建知识库，导入测试文档，检索成功
- 添加记忆，检索记忆成功
- 导入对话文件，提取记忆，更新画像
- 删除会话，确认关联记忆处理正确

### Phase 3: 记忆代理 + 开发平台适配 + UI完善 (2-3周)

**目标:** 记忆代理服务 + 各开发平台适配 + 通道切换界面 + 界面完善

任务:
1. MemoryProxy代理服务实现
2. 通道配置管理（Mem-Switch内控制每个工具的通道）
3. 各平台适配器开发:
   - Claude Code (MCP server方式)
   - Codex (OpenAI兼容API代理)
   - OpenClaw (文件扫描+API适配)
   - OpenCode (工作目录扫描)
   - Gemini CLI (Gemini API代理)
   - Hermes (基础文件扫描，代理后期完善)
4. 记忆注入引擎（检索→组装→注入）
5. 通道切换界面（全局开关 + 各工具独立配置）
6. 知识库管理界面完善
7. 记忆库管理界面完善
8. 对话导入界面完善
9. 设置界面

关键文件:
- `backend/services/memory_proxy.py`
- `backend/services/channel_manager.py`
- `backend/services/memory_injector.py`
- `backend/platform_adapters/claude_code.py`
- `backend/platform_adapters/codex.py`
- `backend/platform_adapters/openclaw.py`
- `backend/platform_adapters/opencode.py`
- `backend/platform_adapters/gemini_cli.py`
- `backend/platform_adapters/hermes.py`
- `frontend/src/views/*.svelte`
- `frontend/src/components/ChannelManagerView.svelte`

验证:
- 通过Mem-Switch界面切换Claude Code通道，记忆自动注入生效
- 通过Mem-Switch界面切换Codex通道，代理转发正常
- 各平台对话文件扫描导入成功
- 全局开关一键切换所有工具通道
- 各界面功能完整

### Phase 4: 打包 + 文档 (1周)

**目标:** 各平台安装包 + README

任务:
1. 各平台安装包制作
2. README编写（对话导入→画像提取流程详解）
3. 用户指南
4. 应用图标/主题
5. 首次发布

关键文件:
- `README.md`
- `docs/user_guide.md`
- `scripts/build-*.sh`

验证:
- Windows .exe安装成功
- MacOS .dmg启动正常
- Linux .AppImage功能完整
- README流程说明清晰可执行

---

## 八、项目目录结构

```
mem-switch-desktop/
├── README.md                          # 项目介绍 + 对话导入流程详解
│
├── frontend/                          # Svelte 5前端
│   ├── src/
│   │   ├── App.svelte                 # 主应用路由
│   │   ├── components/
│   │   │   ├── StartupGuide.svelte    # 首次启动引导(硬件检测)
│   │   │   ├── KnowledgeView.svelte   # 知识库管理
│   │   │   ├── MemoryView.svelte      # 记忆库管理
│   │   │   ├── ImportView.svelte      # 对话导入
│   │   │   ├── ChannelManagerView.svelte # 记忆通道路由(Phase 3)
│   │   │   └── SettingsView.svelte    # 设置
│   │   ├── stores/                    # Svelte runes状态管理
│   │   └── lib/                       # API客户端+工具函数
│   ├── package.json
│   └── vite.config.js
│
├── backend/                           # Python FastAPI后端
│   ├── main.py                        # API入口
│   ├── config.py                      # 配置管理
│   ├── services/
│   │   ├── knowledge_service.py       # 知识库服务
│   │   ├── memory_service.py          # 记忆库服务
│   │   ├── conversation_importer.py   # 对话导入服务
│   │   ├── profile_manager.py         # 用户画像管理
│   │   ├── memory_proxy.py            # 记忆代理(Phase 3)
│   │   ├── channel_manager.py         # 通道配置管理(Phase 3)
│   │   ├── memory_injector.py         # 记忆注入引擎(Phase 3)
│   │   ├── hardware_detector.py       # 硬件检测
│   │   └── vector_store.py            # Qdrant向量库管理
│   ├── adapters/                      # 对话导入数据源适配器
│   │   ├── claude_mem_adapter.py      # claude-mem SQLite
│   │   ├── claude_code_adapter.py     # Claude Code JSONL
│   │   ├── codex_adapter.py           # Codex OpenAI格式
│   │   ├── openclaw_adapter.py        # OpenClaw自定义JSON
│   │   ├── opencode_adapter.py        # OpenCode Markdown/JSON
│   │   ├── gemini_cli_adapter.py      # Gemini CLI Google AI
│   │   ├── hermes_adapter.py          # Hermes NousResearch Agent
│   │   ├── json_file_adapter.py       # JSON文件
│   │   ├── markdown_adapter.py        # Markdown文件
│   │   ├── clipboard_adapter.py       # 剪贴板
│   │   └── generic_adapter.py         # 其他平台通用
│   ├── platform_adapters/             # 记忆代理平台适配器(Phase 3)
│   │   ├── claude_code.py             # Claude Code MCP适配
│   │   ├── codex.py                   # Codex OpenAI API代理
│   │   ├── openclaw.py                # OpenClaw文件+API适配
│   │   ├── opencode.py                # OpenCode工作目录扫描
│   │   ├── gemini_cli.py              # Gemini CLI API代理
│   │   ├── hermes.py                  # Hermes基础适配(仓库: NousResearch/hermes-agent)
│   │   └── base_adapter.py            # 平台适配器基类
│   ├── api/
│   │   ├── routes/
│   │   │   ├── knowledge.py
│   │   │   ├── memory.py
│   │   │   ├── import.py
│   │   │   ├── proxy.py               # 代理路由(Phase 3)
│   │   │   ├── channels.py            # 通道配置路由(Phase 3)
│   │   │   └── settings.py
│   │   └── schemas/
│   │       ├── conversation.py
│   │       ├── memory.py
│   │       ├── knowledge.py
│   │       └── profile.py
│   ├── requirements.txt
│   └── pyproject.toml
│
├── src-tauri/                         # Tauri v2配置
│   ├── tauri.conf.json
│   ├── src/
│   │   └── main.rs                    # Rust入口
│   └── icons/
│
├── scripts/                           # 打包脚本
│   ├── build-windows.ps1
│   ├── build-linux.sh
│   └── build-macos.sh
│
└── docs/
    ├── user_guide.md
    └── installation.md
```

---

## 九、依赖清单

**Python后端:**
```
fastapi>=0.110.0
uvicorn>=0.29.0
mem0ai>=0.1.0
qdrant-client>=1.9.0
ollama>=0.4.0
pyyaml>=6.0
pydantic>=2.6
sqlalchemy>=2.0
python-multipart>=0.0.9
```

**前端:**
```json
{
  "svelte": "^5.0",
  "tailwindcss": "^4.0",
  "@tauri-apps/api": "^2.0",
  "axios": "^1.7"
}
```

---

## 十、云端扩展预留

当前版本纯本地，架构预留以下接口：

```python
# 抽象provider接口
class LLMProvider(Protocol):
    async def generate(self, prompt: str) -> str: ...
    async def embed(self, text: str) -> list[float]: ...

class VectorStoreProvider(Protocol):
    async def search(self, query: list[float], limit: int) -> list[SearchResult]: ...
    async def upsert(self, points: list[PointStruct]) -> None: ...

# 当前实现: OllamaProvider, QdrantProvider
# 后期扩展: OpenAIProvider, CloudQdrantProvider, AnthropicProvider
```

用户通过设置界面切换provider，无需修改核心逻辑。

---

## 十一、README核心内容要求

README必须包含以下流程详解：

1. **对话导入流程**
   - 如何选择数据源
   - 如何预览和确认导入
   - 导入选项说明

2. **记忆提取流程**
   - 提取维度配置（偏好习惯/专业知识/项目上下文）
   - Ollama如何从对话中提取关键信息
   - 提取结果如何写入记忆库

3. **用户画像构建**
   - 画像如何从多次导入中累积更新
   - 画像维度说明
   - 如何手动编辑画像

4. **记忆检索与使用**
   - 单库检索 vs 联合检索
   - 记忆通道路由：Mem-Switch内为各工具配置通道（Phase 3）

5. **开发平台适配**
   - Claude Code / Codex / OpenClaw / OpenCode / Gemini CLI / Hermes (https://github.com/NousResearch/hermes-agent.git)
   - 各平台对话导入方式
   - 通道切换配置方法

6. **硬件自适应**
   - 如何检测硬件配置
   - 模型推荐规则说明
   - 手动覆盖模型选择

---

## 十二、多Agent并行开发

| Agent | 任务 | 阶段 | 依赖 |
|-------|------|------|------|
| Agent A | Phase 1 基础框架 | Phase 1 | 无 |
| Agent B | Phase 2 知识库服务 | Phase 2 | Phase 1 |
| Agent C | Phase 2 记忆库+对话导入 | Phase 2 | Phase 1 |
| Agent D | Phase 3 记忆代理+UI | Phase 3 | Phase 2 |
| Agent E | Phase 4 打包+文档 | Phase 4 | Phase 3 |

Phase 2 的 Agent B 和 Agent C 可并行开发。