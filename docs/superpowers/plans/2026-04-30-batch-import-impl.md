# 批量导入与后台处理实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现批量文件导入、后台任务处理、进度追踪、失败处理、导入去重功能。

**Architecture:** 后端 BatchImportService + TaskQueue + 前端 ImportView 重构。

**Tech Stack:** FastAPI, Svelte 5, asyncio.Semaphore, Chroma, SQLite

---

## 任务分解

### Task 1: 后端 - 数据库扩展

**Files:**
- Modify: `backend/services/database.py`

**目标：** 添加 import_tasks 和 import_task_files 表

- [ ] **Step 1: 添加 import_tasks 表**

```sql
CREATE TABLE IF NOT EXISTS import_tasks (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    total_files INTEGER,
    completed_files INTEGER DEFAULT 0,
    failed_files INTEGER DEFAULT 0,
    skipped_files INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    progress REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);
```

- [ ] **Step 2: 添加 import_task_files 表**

```sql
CREATE TABLE IF NOT EXISTS import_task_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT REFERENCES import_tasks(id),
    file_name TEXT NOT NULL,
    file_path TEXT,
    status TEXT NOT NULL,  -- success/failed/skipped
    error TEXT,
    memories_created INTEGER DEFAULT 0,
    session_id TEXT,
    skipped BOOLEAN DEFAULT 0,
    processed_at DATETIME
);
```

- [ ] **Step 3: 添加索引**

```sql
CREATE INDEX IF NOT EXISTS idx_import_tasks_created ON import_tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_import_task_files_task ON import_task_files(task_id);
```

- [ ] **Step 4: 添加 ORM 模型**

```python
@dataclass
class ImportTask:
    id: str
    source_type: str
    total_files: int
    completed_files: int
    failed_files: int
    skipped_files: int
    status: str
    progress: float
    created_at: datetime
    updated_at: datetime

@dataclass
class ImportTaskFile:
    id: int
    task_id: str
    file_name: str
    file_path: Optional[str]
    status: str
    error: Optional[str]
    memories_created: int
    session_id: Optional[str]
    skipped: bool
    processed_at: Optional[datetime]
```

- [ ] **Step 5: 提交**

```bash
git add backend/services/database.py
git commit -m "feat(import): add import_tasks and import_task_files tables"
```

---

### Task 2: 后端 - BatchImportService

**Files:**
- Create: `backend/services/batch_import_service.py`

**目标：** 实现批量导入服务，支持并发控制和去重检测

- [ ] **Step 1: 创建服务框架**

```python
import asyncio
from typing import List, Dict, Optional
from services.conversation_importer import ConversationImporter
from services.memory_extractor import MemoryExtractor
from services.database import get_session, ImportTask, ImportTaskFile
from datetime import datetime
import uuid

class BatchImportService:
    MAX_CONCURRENT = 2  # 最大并发数
    
    def __init__(self):
        self.importer = ConversationImporter()
        self.extractor = MemoryExtractor()
    
    async def import_batch(
        self,
        source_type: str,
        files: List[str],
        extract_memories: bool = True
    ) -> str:
        """创建批量导入任务，返回 task_id"""
        task_id = str(uuid.uuid4())
        
        # 创建任务记录
        session = get_session()
        task = ImportTask(
            id=task_id,
            source_type=source_type,
            total_files=len(files),
            status="processing",
            progress=0
        )
        # 保存到数据库
        # ...
        session.close()
        
        # 启动后台任务
        asyncio.create_task(self._process_batch(task_id, files, extract_memories))
        
        return task_id
```

- [ ] **Step 2: 实现去重检测**

```python
async def _check_duplicate(self, session_id: str) -> bool:
    """检查会话是否已导入"""
    session = get_session()
    try:
        # 查询 sessions 表
        cursor = session.execute(
            "SELECT id FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        return cursor.fetchone() is not None
    finally:
        session.close()
```

- [ ] **Step 3: 实现文件处理（带信号量）**

```python
async def _process_file(
    self,
    task_id: str,
    file_path: str,
    semaphore: asyncio.Semaphore
) -> Dict:
    """处理单个文件，使用信号量限制并发"""
    async with semaphore:
        try:
            # 解析文件获取 session_id
            conversations = await self.importer.parse_file(file_path)
            
            if not conversations:
                return {"status": "failed", "error": "无法解析文件"}
            
            # 检查是否已导入
            for conv in conversations:
                if await self._check_duplicate(conv.session_id):
                    return {"status": "skipped", "session_id": conv.session_id}
            
            # 执行导入
            result = await self.importer.import_conversations([conv])
            
            return {
                "status": "success",
                "session_id": conv.session_id,
                "memories_created": result.memories_count
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}
```

- [ ] **Step 4: 实现批量处理**

```python
async def _process_batch(
    self,
    task_id: str,
    files: List[str],
    extract_memories: bool
):
    """处理整个批次"""
    semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)
    
    completed = 0
    failed = 0
    skipped = 0
    
    for file_path in files:
        result = await self._process_file(task_id, file_path, semaphore)
        
        if result["status"] == "success":
            completed += 1
        elif result["status"] == "skipped":
            skipped += 1
        else:
            failed += 1
        
        # 更新进度
        await self._update_task_progress(task_id, completed, failed, skipped, len(files))
    
    # 完成任务
    self._complete_task(task_id, completed, failed, skipped)
```

- [ ] **Step 5: 提交**

```bash
git add backend/services/batch_import_service.py
git commit -m "feat(import): add BatchImportService with concurrency control and deduplication"
```

---

### Task 3: 后端 - API 路由

**Files:**
- Modify: `backend/api/routes/import_routes.py`
- Create: `backend/api/schemas/import_task.py`

**目标：** 添加批量导入 API

- [ ] **Step 1: 创建 Schema**

```python
from pydantic import BaseModel
from typing import List, Optional

class BatchImportRequest(BaseModel):
    source_type: str
    files: List[str]
    extract_memories: bool = True

class BatchImportResponse(BaseModel):
    task_id: str
    status: str

class TaskStatusResponse(BaseModel):
    id: str
    status: str
    progress: float
    total_files: int
    completed_files: int
    failed_files: int
    skipped_files: int
```

- [ ] **Step 2: 添加路由**

```python
@router.post("/batch")
async def batch_import(req: BatchImportRequest):
    """批量导入"""
    task_id = await batch_import_service.import_batch(
        req.source_type,
        req.files,
        req.extract_memories
    )
    return {"task_id": task_id, "status": "queued"}

@router.get("/tasks")
async def list_tasks():
    """获取任务列表"""
    tasks = batch_import_service.list_tasks()
    return {"tasks": tasks}

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    task = batch_import_service.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task

@router.post("/tasks/{task_id}/retry")
async def retry_failed(task_id: str):
    """重试失败的文件"""
    new_task_id = await batch_import_service.retry_failed(task_id)
    return {"task_id": new_task_id}
```

- [ ] **Step 3: 提交**

```bash
git add backend/api/routes/import_routes.py backend/api/schemas/import_task.py
git commit -m "feat(import): add batch import API routes"
```

---

### Task 4: 前端 - API 扩展

**Files:**
- Modify: `frontend/src/lib/api.js`

**目标：** 添加批量导入 API 方法

- [ ] **Step 1: 添加 import API**

```javascript
export const api = {
  // ... existing ...
  
  import: {
    // ... existing ...
    
    // 批量导入
    batch: (sourceType, files) => getApi().post('/api/import/batch', {
      source_type: sourceType,
      files
    }),
    
    // 获取任务列表
    listTasks: () => getApi().get('/api/import/tasks'),
    
    // 获取任务状态
    getTaskStatus: (taskId) => getApi().get(`/api/import/tasks/${taskId}`),
    
    // 重试失败
    retryFailed: (taskId) => getApi().post(`/api/import/tasks/${taskId}/retry`),
  },
};
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/lib/api.js
git commit -m "feat(import): add batch import API methods"
```

---

### Task 5: 前端 - ImportView 重构

**Files:**
- Modify: `frontend/src/components/ImportView.svelte`

**目标：** 支持多文件选择和批量导入

- [ ] **Step 1: 添加多文件选择**

```svelte
<script>
  import { api } from '../lib/api.js';
  import { addToast } from '../stores/toast.svelte.js';
  import DragDropZone from './import/DragDropZone.svelte';
  import FileList from './import/FileList.svelte';
  import BatchProgress from './import/BatchProgress.svelte';

  let sourceType = $state('claude_code');
  let selectedFiles = $state([]);
  let importing = $state(false);
  let currentTask = $state(null);
  let progress = $state({ total: 0, completed: 0, failed: 0, skipped: 0 });

  function handleFilesSelect(files) {
    selectedFiles = [...selectedFiles, ...files];
  }

  function removeFile(index) {
    selectedFiles = selectedFiles.filter((_, i) => i !== index);
  }

  async function startBatchImport() {
    importing = true;
    try {
      const resp = await api.import.batch(sourceType, selectedFiles.map(f => f.path));
      currentTask = resp.data.task_id;
      addToast(`批量导入已开始，${selectedFiles.length} 个文件`, 'success');
      
      // 轮询任务状态
      pollTaskStatus(currentTask);
    } catch (e) {
      addToast('导入失败：' + e.message, 'error');
    }
  }

  async function pollTaskStatus(taskId) {
    while (importing) {
      const resp = await api.import.getTaskStatus(taskId);
      const data = resp.data;
      
      progress = {
        total: data.total_files,
        completed: data.completed_files,
        failed: data.failed_files,
        skipped: data.skipped_files
      };
      
      if (data.status === 'completed' || data.status === 'failed') {
        importing = false;
        if (data.status === 'completed') {
          addToast(`导入完成：${data.completed_files} 成功，${data.skipped_files} 跳过，${data.failed_files} 失败`, 'success');
        }
        break;
      }
      
      await new Promise(r => setTimeout(r, 2000));
    }
  }
</script>
```

- [ ] **Step 2: 添加文件列表组件**

```svelte
<!-- 文件列表 -->
{#if selectedFiles.length > 0}
  <FileList files={selectedFiles} onRemove={removeFile} />
{/if}
```

- [ ] **Step 3: 添加进度显示**

```svelte
{#if importing}
  <BatchProgress 
    total={progress.total}
    completed={progress.completed}
    failed={progress.failed}
    skipped={progress.skipped}
  />
{/if}
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/ImportView.svelte
git commit -m "feat(import): refactor ImportView for batch import"
```

---

### Task 6: 前端 - 辅助组件

**Files:**
- Create: `frontend/src/components/import/FileList.svelte`
- Create: `frontend/src/components/import/BatchProgress.svelte`

**目标：** 创建文件列表和进度显示组件

- [ ] **Step 1: 创建 FileList 组件**

```svelte
<script>
  let { files = [], onRemove } = $props();

  function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }
</script>

<div class="border rounded-lg divide-y">
  {#each files as file, i}
    <div class="flex items-center justify-between p-3">
      <div class="flex items-center gap-3">
        <span class="text-lg">📄</span>
        <div>
          <div class="font-medium">{file.name}</div>
          <div class="text-xs text-gray-500">{formatSize(file.size)}</div>
        </div>
      </div>
      <button 
        class="text-gray-400 hover:text-red-500"
        onclick={() => onRemove(i)}
      >
        ×
      </button>
    </div>
  {/each}
</div>
```

- [ ] **Step 2: 创建 BatchProgress 组件**

```svelte
<script>
  let { total, completed, failed, skipped } = $props();

  $ progressPercent = total > 0 ? ((completed + failed + skipped) / total) * 100 : 0;
</script>

<div class="space-y-3">
  <!-- 总体进度条 -->
  <div>
    <div class="flex justify-between text-sm mb-1">
      <span>进度</span>
      <span>{completed + failed + skipped} / {total}</span>
    </div>
    <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
      <div 
        class="h-full bg-blue-500 transition-all"
        style="width: {progressPercent}%"
      />
    </div>
  </div>

  <!-- 状态统计 -->
  <div class="flex gap-4 text-sm">
    <span class="text-green-600">✓ 完成 {completed}</span>
    <span class="text-amber-600">⊘ 跳过 {skipped}</span>
    <span class="text-red-600">✗ 失败 {failed}</span>
  </div>
</div>
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/import/FileList.svelte frontend/src/components/import/BatchProgress.svelte
git commit -m "feat(import): add FileList and BatchProgress components"
```

---

### Task 7: 集成测试

**Files:**
- 测试所有功能

- [ ] **Step 1: 前端构建测试**

```bash
cd /home/wchao/workspace/Date_LIB/frontend && npm run build
```

- [ ] **Step 2: 后端导入测试**

```bash
cd /home/wchao/workspace/Date_LIB/backend && python -c "
from services.batch_import_service import BatchImportService
from api.routes.import_routes import router
print('Batch import service and routes OK')
"
```

- [ ] **Step 3: 功能测试**

1. 选择 5 个文件导入 → 观察并发数为 2
2. 导入已存在的会话 → 验证跳过计数
3. 查看任务状态 → 进度正确更新

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "feat: implement batch import with deduplication and progress tracking"
```

---

## 验证清单

- [ ] 多文件选择正常工作
- [ ] 并发数限制为 2
- [ ] 已导入的会话自动跳过
- [ ] 进度显示正确（完成/跳过/失败）
- [ ] 前端构建成功
- [ ] 后端服务导入无错误

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-30-batch-import-impl.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - 每个任务派发一个子 agent，期间审查，快速迭代

**2. Inline Execution** - 在本会话中使用 executing-plans 批量执行，带检查点

**Which approach?**
