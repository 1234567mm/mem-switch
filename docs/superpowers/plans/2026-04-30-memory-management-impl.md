# 记忆管理增强实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 增强记忆管理能力，新增编辑、合并、失效/过期、使用统计功能。

**Architecture:** 后端 MemoryService 扩展 + Chroma 向量库字段扩展 + 前端 MemoryView 增强。

**Tech Stack:** FastAPI, Svelte 5, Chroma (向量存储), SQLite (元数据)

---

## 文件结构

### 后端修改

```
backend/
├── services/
│   ├── memory_service.py     # 修改：扩展 Memory dataclass，增加方法
│   └── memory_injector.py    # 修改：注入时更新 call_count
├── api/routes/
│   └── memory.py             # 修改：添加编辑/删除/失效/合并 API
└── config.py                 # 修改：添加过期天数配置
```

### 前端修改

```
frontend/src/
├── components/
│   ├── MemoryView.svelte          # 修改：添加按钮和功能
│   └── memory/
│       ├── MemoryEditModal.svelte    # 新增：编辑记忆弹窗
│       └── MemoryMergeSuggestions.svelte  # 新增：合并建议面板
├── stores/
│   └── memory.svelte.js           # 新增：记忆状态管理
└── lib/
    └── api.js                    # 修改：添加记忆管理 API
```

---

## 任务分解

### Task 1: 后端 - Memory 模型扩展

**Files:**
- Modify: `backend/services/memory_service.py`

- [ ] **Step 1: 扩展 Memory dataclass**

```python
# Memory dataclass 新增字段
@dataclass
class Memory:
    memory_id: str
    type: str
    content: str
    dimensions: dict
    confidence: float = 0.8
    source_session_id: Optional[str] = None
    created_at: datetime = None
    # 新增字段
    invalidated: bool = False           # 是否失效
    expires_at: Optional[datetime] = None  # 过期时间
    call_count: int = 0                # 调用次数
    last_called_at: Optional[datetime] = None  # 最后调用时间
```

- [ ] **Step 2: 添加 update_memory 方法**

```python
def update_memory(self, memory_id: str, content: str = None,
                  memory_type: str = None, dimensions: dict = None) -> Memory:
    """更新记忆"""
    # 获取现有记忆
    memories = self.search_memories(memory_id)
    if not memories:
        raise ValueError(f"Memory {memory_id} not found")

    memory = memories[0]

    # 更新字段
    if content is not None:
        memory.content = content
        # 重新生成 embedding
        memory.embeddings = self.ollama.embed(content)

    if memory_type is not None:
        memory.type = memory_type

    if dimensions is not None:
        memory.dimensions = dimensions

    # 更新到向量库
    self.vector_store.upsert(collection="memories", points=[{
        "id": memory.memory_id,
        "vector": memory.embeddings,
        "payload": {
            "type": memory.type,
            "dimensions": memory.dimensions,
            "confidence": memory.confidence,
            "source_session_id": memory.source_session_id,
            "created_at": memory.created_at.isoformat() if memory.created_at else None,
            "invalidated": memory.invalidated,
            "expires_at": memory.expires_at.isoformat() if memory.expires_at else None,
            "call_count": memory.call_count,
            "last_called_at": memory.last_called_at.isoformat() if memory.last_called_at else None,
        }
    }])

    return memory
```

- [ ] **Step 3: 添加 invalidate_memory 方法**

```python
def invalidate_memory(self, memory_id: str, invalidate: bool = True) -> bool:
    """标记记忆失效/恢复"""
    try:
        self.vector_store.updatePayload(
            collection="memories",
            point_id=memory_id,
            payload={"invalidated": invalidate}
        )
        return True
    except Exception:
        return False
```

- [ ] **Step 4: 添加 increment_call_count 方法**

```python
def increment_call_count(self, memory_id: str) -> bool:
    """增加记忆调用计数"""
    try:
        memory = self._get_memory_by_id(memory_id)
        if not memory:
            return False

        memory.call_count = (memory.call_count or 0) + 1
        memory.last_called_at = datetime.now()

        self.vector_store.updatePayload(
            collection="memories",
            point_id=memory_id,
            payload={
                "call_count": memory.call_count,
                "last_called_at": memory.last_called_at.isoformat()
            }
        )
        return True
    except Exception:
        return False
```

- [ ] **Step 5: 添加 get_memory_stats 方法**

```python
def get_memory_stats(self, memory_id: str) -> dict:
    """获取记忆统计"""
    memory = self._get_memory_by_id(memory_id)
    if not memory:
        return None
    return {
        "call_count": memory.call_count or 0,
        "last_called_at": memory.last_called_at.isoformat() if memory.last_called_at else None
    }
```

- [ ] **Step 6: 修改 search_memories 过滤失效记忆**

在 `search_memories` 方法中，向 Chroma 查询时添加 `invalidated == False` 过滤条件。

```python
# 在 vector_store.search 调用中添加 filter
filter_dict = {"invalidated": {"$eq": False}} if not include_invalidated else None
```

- [ ] **Step 7: 提交**

```bash
git add backend/services/memory_service.py
git commit -m "feat(memory): extend Memory model with stats and invalidate fields"
```

---

### Task 2: 后端 - Memory API 路由

**Files:**
- Modify: `backend/api/routes/memory.py`

- [ ] **Step 1: 读取现有 memory.py 路由**

```bash
cat /home/wchao/workspace/Date_LIB/backend/api/routes/memory.py
```

- [ ] **Step 2: 添加新的 Pydantic 模型**

```python
from pydantic import BaseModel
from typing import Optional

class MemoryUpdateRequest(BaseModel):
    content: Optional[str] = None
    memory_type: Optional[str] = None
    dimensions: Optional[dict] = None

class MemoryStatsResponse(BaseModel):
    call_count: int
    last_called_at: Optional[str]
```

- [ ] **Step 3: 添加路由**

```python
@router.patch("/{memory_id}")
async def update_memory(memory_id: str, req: MemoryUpdateRequest):
    """更新记忆"""
    try:
        memory = memory_service.update_memory(
            memory_id,
            content=req.content,
            memory_type=req.memory_type,
            dimensions=req.dimensions
        )
        return {"status": "success", "memory": memory}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{memory_id}/invalidate")
async def invalidate_memory(memory_id: str, invalidate: bool = True):
    """标记记忆失效/恢复"""
    success = memory_service.invalidate_memory(memory_id, invalidate)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update memory")
    return {"status": "success"}

@router.get("/{memory_id}/stats")
async def get_memory_stats(memory_id: str):
    """获取记忆统计"""
    stats = memory_service.get_memory_stats(memory_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Memory not found")
    return stats
```

- [ ] **Step 4: 提交**

```bash
git add backend/api/routes/memory.py
git commit -m "feat(memory): add update, invalidate, and stats API routes"
```

---

### Task 3: 前端 - API 扩展

**Files:**
- Modify: `frontend/src/lib/api.js`

- [ ] **Step 1: 添加记忆管理 API**

在 api.js 中添加：

```javascript
memory: {
  // ... existing APIs ...
  update: (id, data) => getApi().patch(`/api/memory/${id}`, data),
  invalidate: (id, invalidate) => getApi().post(`/api/memory/${id}/invalidate`, { invalidate }),
  getStats: (id) => getApi().get(`/api/memory/${id}/stats`),
},
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/lib/api.js
git commit -m "feat(memory): add memory management API methods"
```

---

### Task 4: 前端 - Memory 状态管理

**Files:**
- Create: `frontend/src/stores/memory.svelte.js`

- [ ] **Step 1: 创建 memory 状态管理**

```javascript
let memoryState = $state({
  memories: [],
  selectedMemory: null,
  editingMemory: null,
  mergeSuggestions: [],
  loading: false
});

export function selectMemory(memory) {
  memoryState.selectedMemory = memory;
}

export function setEditingMemory(memory) {
  memoryState.editingMemory = memory;
}

export function clearEditingMemory() {
  memoryState.editingMemory = null;
}

export function updateMemoryInList(memoryId, updates) {
  memoryState.memories = memoryState.memories.map(m =>
    m.memory_id === memoryId ? { ...m, ...updates } : m
  );
}

export function removeMemoryFromList(memoryId) {
  memoryState.memories = memoryState.memories.filter(m => m.memory_id !== memoryId);
}

export { memoryState };
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/stores/memory.svelte.js
git commit -m "feat(memory): add memory state management"
```

---

### Task 5: 前端 - MemoryEditModal 组件

**Files:**
- Create: `frontend/src/components/memory/MemoryEditModal.svelte`

- [ ] **Step 1: 创建编辑弹窗组件**

```svelte
<script>
  import { api } from '../../lib/api.js';
  import { updateMemoryInList } from '../../stores/memory.svelte.js';
  import { addToast } from '../../stores/toast.svelte.js';

  let { memory, onClose } = $props();

  let content = $state(memory.content);
  let memoryType = $state(memory.type);
  let saving = $state(false);

  const types = [
    { value: 'preference', label: '偏好习惯' },
    { value: 'expertise', label: '专业知识' },
    { value: 'project_context', label: '项目上下文' },
  ];

  async function handleSave() {
    saving = true;
    try {
      await api.memory.update(memory.memory_id, {
        content,
        memory_type: memoryType
      });
      updateMemoryInList(memory.memory_id, { content, type: memoryType });
      addToast('记忆已更新', 'success');
      onClose();
    } catch (e) {
      addToast('更新失败: ' + e.message, 'error');
    }
    saving = false;
  }
</script>

<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
  <div class="bg-white rounded-xl p-6 w-full max-w-lg">
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-lg font-semibold">编辑记忆</h3>
      <button class="text-gray-400 hover:text-gray-600" onclick={onClose}>×</button>
    </div>

    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium mb-1">类型</label>
        <select
          bind:value={memoryType}
          class="w-full p-2 border rounded-lg"
        >
          {#each types as t}
            <option value={t.value}>{t.label}</option>
          {/each}
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium mb-1">内容</label>
        <textarea
          bind:value={content}
          class="w-full p-2 border rounded-lg h-40"
          placeholder="记忆内容..."
        ></textarea>
      </div>
    </div>

    <div class="flex justify-end gap-3 mt-6">
      <button class="btn-secondary" onclick={onClose}>取消</button>
      <button
        class="btn-primary"
        disabled={saving}
        onclick={handleSave}
      >
        {saving ? '保存中...' : '保存'}
      </button>
    </div>
  </div>
</div>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/memory/MemoryEditModal.svelte
git commit -m "feat(memory): add MemoryEditModal component"
```

---

### Task 6: 前端 - MemoryView 增强

**Files:**
- Modify: `frontend/src/components/MemoryView.svelte`

- [ ] **Step 1: 读取现有 MemoryView**

```bash
cat /home/wchao/workspace/Date_LIB/frontend/src/components/MemoryView.svelte
```

- [ ] **Step 2: 添加编辑/失效按钮到记忆卡片**

在记忆卡片中添加按钮：
```svelte
<!-- 记忆卡片中的按钮 -->
<div class="flex gap-2 mt-2">
  <button
    class="text-xs text-blue-500 hover:underline"
    onclick={() => setEditingMemory(memory)}
  >
    编辑
  </button>
  <button
    class="text-xs text-amber-500 hover:underline"
    onclick={() => handleInvalidate(memory.memory_id)}
  >
    {memory.invalidated ? '恢复' : '失效'}
  </button>
  <button
    class="text-xs text-red-500 hover:underline"
    onclick={() => handleDelete(memory.memory_id)}
  >
    删除
  </button>
</div>
```

- [ ] **Step 3: 添加统计显示**

```svelte
<!-- 记忆卡片底部 -->
{#if memory.call_count > 0}
  <div class="text-xs text-gray-400 mt-1">
    调用 {memory.call_count} 次
    {memory.last_called_at ? `· 最后调用 ${formatTime(memory.last_called_at)}` : ''}
  </div>
{/if}
```

- [ ] **Step 4: 集成 MemoryEditModal**

```svelte
<script>
  import MemoryEditModal from './memory/MemoryEditModal.svelte';
  // ...
  let editingMemory = $state(null);
</script>

{#if editingMemory}
  <MemoryEditModal
    memory={editingMemory}
    onClose={() => editingMemory = null}
  />
{/if}
```

- [ ] **Step 5: 添加处理函数**

```javascript
async function handleInvalidate(memoryId) {
  try {
    await api.memory.invalidate(memoryId, true);
    updateMemoryInList(memoryId, { invalidated: true });
    addToast('记忆已标记失效', 'success');
  } catch (e) {
    addToast('操作失败', 'error');
  }
}

async function handleDelete(memoryId) {
  if (!confirm('确定要删除这条记忆吗？')) return;
  try {
    await api.memory.delete(memoryId);
    removeMemoryFromList(memoryId);
    addToast('记忆已删除', 'success');
  } catch (e) {
    addToast('删除失败', 'error');
  }
}
```

- [ ] **Step 6: 提交**

```bash
git add frontend/src/components/MemoryView.svelte
git commit -m "feat(memory): enhance MemoryView with edit and invalidate buttons"
```

---

### Task 7: 合并建议功能（可选，简化版）

**Files:**
- Create: `frontend/src/components/memory/MemoryMergeSuggestions.svelte`

- [ ] **Step 1: 创建合并建议组件**

由于 AI 合并建议需要更复杂的实现，先创建一个简化版：显示相似记忆供用户手动选择合并。

```svelte
<script>
  let { memories = [], onMerge } = $props();

  let selectedIds = $state([]);

  function toggleSelect(id) {
    if (selectedIds.includes(id)) {
      selectedIds = selectedIds.filter(i => i !== id);
    } else {
      selectedIds = [...selectedIds, id];
    }
  }

  function handleMerge() {
    if (selectedIds.length < 2) {
      alert('请选择至少两条记忆进行合并');
      return;
    }
    onMerge(selectedIds);
  }
</script>

<div class="card p-4">
  <h4 class="font-medium mb-3">相似记忆建议</h4>
  <p class="text-sm text-gray-500 mb-3">选择要合并的记忆（至少2条）</p>

  <div class="space-y-2 mb-4">
    {#each memories as memory}
      <div
        class="p-3 border rounded-lg cursor-pointer {selectedIds.includes(memory.memory_id) ? 'border-blue-500 bg-blue-50' : ''}"
        onclick={() => toggleSelect(memory.memory_id)}
      >
        <div class="flex items-center gap-2">
          <input
            type="checkbox"
            checked={selectedIds.includes(memory.memory_id)}
            onclick.stop
            onchange={() => toggleSelect(memory.memory_id)}
          />
          <span class="badge badge-info">{memory.type}</span>
        </div>
        <p class="text-sm mt-2 line-clamp-2">{memory.content}</p>
      </div>
    {/each}
  </div>

  <button
    class="btn-primary w-full"
    disabled={selectedIds.length < 2}
    onclick={handleMerge}
  >
    合并选中记忆
  </button>
</div>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/memory/MemoryMergeSuggestions.svelte
git commit -m "feat(memory): add MemoryMergeSuggestions component"
```

---

### Task 8: 集成测试

**Files:**
- 测试所有功能

- [ ] **Step 1: 前端构建测试**

```bash
cd /home/wchao/workspace/Date_LIB/frontend && npm run build
```

- [ ] **Step 2: 后端导入测试**

```bash
cd /home/wchao/workspace/Date_LIB/backend && python -c "
from services.memory_service import MemoryService
from api.routes.memory import router
print('Memory service and routes OK')
"
```

- [ ] **Step 3: Git 提交**

```bash
git add -A
git commit -m "feat: implement memory management enhancement

- Add memory update, invalidate, and stats APIs
- Add MemoryEditModal for editing memories
- Enhance MemoryView with edit/invalidate/delete buttons
- Add memory call_count and last_called_at tracking
- Add MemoryMergeSuggestions component"
```

---

## 验证清单

- [ ] 编辑记忆 → 保存成功，内容更新
- [ ] 标记记忆失效 → 搜索不到该记忆
- [ ] 恢复记忆 → 记忆重新可搜索
- [ ] 删除记忆 → 记忆从列表移除
- [ ] 记忆被调用 → call_count 增加
- [ ] 前端构建成功

---

## 备选实施顺序

如果 Task 2（API 路由）有问题，可以先完成 Task 1，然后测试服务层，再继续。

**Plan complete and saved to `docs/superpowers/plans/2026-04-30-memory-management-impl.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
