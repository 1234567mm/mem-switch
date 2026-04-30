# 批量导入与后台处理设计文档

## 概述

增强 Mem-Switch 的对话导入功能，支持批量文件导入、后台任务处理、进度追踪、失败处理、**导入去重**，同时优化系统资源占用。

## 功能清单

### 1. 批量文件导入

**按平台选择**：
- 用户选择数据源平台（Claude Code / Codex / OpenCode / Gemini CLI 等）
- 一次选择多个文件
- 支持拖拽添加文件

**导入去重**：
- 根据 session_id 判断是否已导入
- 已导入的会话自动跳过
- 显示跳过数量：`导入 3 个，跳过 5 个（已存在），失败 1 个`

**资源优化**：
- 限制并发处理数：2 个文件同时处理
- 其余文件排队等待
- 避免 CPU/内存峰值

### 2. 后台任务处理

**任务队列**：
- 使用现有 `TaskQueue` 服务
- 每个批量导入创建一个父任务
- 每个文件创建一个子任务

**任务状态**：
```
queued → processing → completed/failed
           ↓
        progress: 0-100%
```

**进度追踪**：
- 前端轮询任务状态（每 2 秒）
- 显示总体进度：`正在处理：3/10`
- 显示当前文件进度条

### 3. 失败处理

**部分保留策略**：
- 成功的文件：保留导入的记忆和对话
- 失败的文件：记录错误原因
- 已导入的会话：自动跳过，不重复导入
- 用户可选择重试失败文件

**去重检测**：
- 解析文件时提取 session_id
- 查询 SQLite sessions 表检查是否存在
- 已存在的会话标记为 `skipped`，计入跳过数量

**错误类型**：
- 文件格式错误
- 解析失败
- 内存提取失败
- Ollama 连接超时

### 4. 导入历史

**记录内容**：
- 任务 ID、平台、文件列表
- 开始/结束时间
- 成功/失败计数
- 导入的记忆数量

**操作**：
- 查看导入详情
- 删除任务记录
- 删除关联记忆（可选）

## 后端 API 设计

### 新增端点

```
POST /api/import/batch
  Body: { "source_type": "string", "files": ["file1", "file2"] }
  Response: { "task_id": "uuid", "status": "queued" }

GET /api/import/tasks
  Response: { "tasks": [{ "id", "status", "progress", "created_at", ... }] }

GET /api/import/tasks/{id}
  Response: { 
    "id", "status", "progress", 
    "total_files", "completed_files", "failed_files", "skipped_files",
    "results": [{ "file", "status", "error", "memories_created", "skipped" }]
  }

POST /api/import/tasks/{id}/retry
  Body: { "file_indices": [0, 2] }  # 重试失败的文件
  Response: { "task_id": "new_uuid" }

DELETE /api/import/tasks/{id}
  Query: { "keep_memories": true/false }
  Response: { "status": "deleted" }
```

### 修改端点

```
POST /api/import/upload
  修改为：支持多文件上传，返回 task_id
```

## 后端服务设计

### BatchImportService

```python
class BatchImportService:
    MAX_CONCURRENT = 2  # 最大并发数
    
    async def import_batch(
        self,
        source_type: str,
        files: list[str],
        extract_memories: bool = True
    ) -> str:
        """创建批量导入任务，返回 task_id"""
        
    async def _check_duplicate(self, session_id: str) -> bool:
        """检查会话是否已导入"""
        
    async def _process_file(
        self,
        task_id: str,
        file_path: str,
        semaphore: asyncio.Semaphore
    ) -> dict:
        """处理单个文件，使用信号量限制并发
        返回：{ status: "success/failed/skipped", ... }
        """
        
    async def _update_task_progress(
        self,
        task_id: str,
        completed: int,
        failed: int,
        skipped: int,
        total: int
    ):
        """更新任务进度"""
```

### TaskQueue 扩展

```python
@dataclass
class BatchTask:
    task_id: str
    source_type: str
    files: list[str]
    status: TaskStatus
    progress: float  # 0-100
    total_files: int
    completed_files: int
    failed_files: int
    skipped_files: int  # 跳过数量（已存在）
    results: list[FileResult]
    created_at: datetime
    updated_at: datetime

@dataclass
class FileResult:
    file_name: str
    status: str  # success/failed/skipped
    error: Optional[str]
    memories_created: int
    session_id: Optional[str]
```

## 前端组件设计

### ImportView 重构

```svelte
<!-- 多文件选择 -->
<DropZone multiple onFilesSelect={handleFilesSelect} />

<!-- 平台选择 -->
<PlatformSelector bind:value={sourceType} />

<!-- 文件列表 -->
<FileList files={selectedFiles} onRemove={removeFile} />

<!-- 导入按钮 -->
<Button onclick={startBatchImport} disabled={files.length === 0}>
  导入 {files.length} 个文件
</Button>

<!-- 进度显示 -->
{#if importing}
  <BatchProgress 
    {total} 
    {completed} 
    {failed}
    {skipped}
    currentFile={currentFile}
  />
{/if}
```

### BatchProgress 组件

```svelte
<!-- 总体进度 -->
<div class="progress-bar">
  <div style="width: {(completed / total) * 100}%" />
</div>
<div>{completed} / {total} 完成</div>

<!-- 当前文件进度 -->
{#if currentFile}
  <div class="file-progress">
    正在处理：{currentFile.name}
    <div class="spinner" />
  </div>
{/if}

<!-- 失败提示 -->
{#if failed > 0}
  <div class="error-summary">
    {failed} 个文件失败，<a onclick={showFailed}>查看详情</a>
  </div>
{/if}

<!-- 跳过提示 -->
{#if skipped > 0}
  <div class="info-summary">
    {skipped} 个文件已跳过（已导入）
  </div>
{/if}
```

## 资源优化策略

### 并发控制

```python
# 使用信号量限制并发
semaphore = asyncio.Semaphore(2)

async with semaphore:
    result = await process_file(file)
```

### 内存管理

- 流式读取大文件（不一次性加载）
- 处理完每个文件后释放内存
- 限制向量嵌入批次大小（每次最多 100 条）

### CPU 限制

- 避免同时调用多个 LLM
- 串行化 memory extraction
- 使用 Ollama 的批处理 API（如果支持）

## 数据库变更

### 新增表

```sql
CREATE TABLE import_tasks (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    total_files INTEGER,
    completed_files INTEGER DEFAULT 0,
    failed_files INTEGER DEFAULT 0,
    status TEXT NOT NULL,  -- queued/processing/completed/failed
    progress REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE import_task_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT REFERENCES import_tasks(id),
    file_name TEXT NOT NULL,
    file_path TEXT,
    status TEXT NOT NULL,  -- success/failed
    error TEXT,
    memories_created INTEGER DEFAULT 0,
    session_id TEXT,
    processed_at DATETIME
);

CREATE INDEX idx_import_tasks_created ON import_tasks(created_at DESC);
CREATE INDEX idx_import_task_files_task ON import_task_files(task_id);
```

## 实施顺序

1. **Phase 1**: 后端 - 数据库表 + BatchImportService
2. **Phase 2**: 后端 - API 路由 + TaskQueue 集成
3. **Phase 3**: 前端 - ImportView 重构 + 多文件选择
4. **Phase 4**: 前端 - 进度显示 + 错误处理
5. **Phase 5**: 集成测试 + 性能优化

## 验证方式

1. 选择 10 个文件导入 → 观察并发数为 2
2. 导入过程中查看任务状态 → 进度正确更新
3. 导入已存在的会话 → 自动跳过，显示 skipped_count
4. 模拟失败文件 → 验证部分保留策略
5. 重试失败文件 → 验证重试功能
6. 监控系统资源 → CPU/内存使用合理
