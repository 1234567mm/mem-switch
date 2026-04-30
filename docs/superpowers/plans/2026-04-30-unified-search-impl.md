# 统一搜索中心实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现统一搜索中心，支持跨记忆库、知识库的统一搜索，包含搜索历史和热门推荐功能。

**Architecture:** 前端搜索面板 + 后端统一搜索 API。前端发起并行查询，后端聚合结果返回。搜索历史和热门计数存储在 SQLite。

**Tech Stack:** FastAPI (后端), Svelte 5 (前端), SQLite (数据), ChromaDB (向量存储)

---

## 文件结构

### 后端新增/修改

```
backend/
├── api/routes/
│   └── search.py          # 新增: 搜索相关 API
├── services/
│   └── search_service.py  # 新增: 搜索服务
└── database.py            # 修改: 新增表和字段
```

### 前端新增/修改

```
frontend/src/
├── components/
│   └── search/
│       ├── SearchPanel.svelte      # 新增
│       ├── SearchInput.svelte     # 新增
│       ├── ScopeSelector.svelte   # 新增
│       ├── SearchResults.svelte   # 新增
│       ├── SearchHistory.svelte   # 新增
│       └── HotItems.svelte        # 新增
├── stores/
│   └── search.svelte.js           # 新增
└── lib/
    └── api.js                     # 修改
```

---

## 任务分解

### Task 1: 后端 - 数据库变更

**Files:**
- Modify: `backend/database.py`

- [ ] **Step 1: 在 database.py 中添加 search_history 表创建**

```python
# 在 init_db 函数中添加
def init_db():
    # ... existing tables ...
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_search_history_timestamp
        ON search_history(timestamp DESC)
    """)
```

- [ ] **Step 2: 在 Memory 模型中添加 call_count 字段**

```python
# 在 Memory 类中添加
call_count = Column(Integer, default=0)
```

- [ ] **Step 3: 在 Document 模型中添加 view_count 字段**

```python
# 在 Document 类中添加
view_count = Column(Integer, default=0)
```

- [ ] **Step 4: 运行数据库迁移**

Run: `cd /home/wchao/workspace/Date_LIB/backend && python -c "from database import init_db; init_db()"`

- [ ] **Step 5: 提交**

```bash
git add backend/database.py
git commit -m "feat(search): add search_history table and count fields"
```

---

### Task 2: 后端 - 搜索服务

**Files:**
- Create: `backend/services/search_service.py`

- [ ] **Step 1: 创建 search_service.py**

```python
from sqlalchemy.orm import Session
from database import get_session, Memory, Document, KnowledgeBase, search_history as SearchHistoryTable
from services.vector_store import VectorStore
from services.ollama_service import OllamaService
from datetime import datetime
import json

class SearchService:
    def __init__(self):
        self.vector_store = VectorStore()
        self.ollama = OllamaService()

    def unified_search(self, query: str, scopes: list, limit: int = 20) -> dict:
        """统一搜索入口"""
        results = {}
        session = get_session()

        try:
            if "memory" in scopes:
                results["memory"] = self.search_memories(query, limit, session)
                self.add_search_history(query)

            if "knowledge" in scopes:
                results["knowledge"] = self.search_knowledge(query, limit, session)

            return results
        finally:
            session.close()

    def search_memories(self, query: str, limit: int, session: Session) -> dict:
        """搜索记忆库"""
        start_time = datetime.now()

        # 小数据量：直接 LIKE 搜索
        memories = session.query(Memory).filter(
            Memory.content.like(f"%{query}%")
        ).order_by(Memory.created_at.desc()).limit(limit).all()

        # 检查数据量决定是否使用向量搜索
        total = session.query(Memory).count()
        if total >= 1000:
            # 大数据量：使用向量搜索
            try:
                embedding = self.ollama.embed(query)
                vector_results = self.vector_store.search(
                    collection="memories",
                    query_embedding=embedding,
                    limit=limit
                )
                # 合并结果
                memory_ids = [r["id"] for r in vector_results]
                if memory_ids:
                    memories = session.query(Memory).filter(
                        Memory.id.in_(memory_ids)
                    ).all()
            except Exception:
                pass  # 向量搜索失败时回退到 LIKE

        items = [{
            "id": m.id,
            "content": m.content[:200],  # 截断显示
            "memory_type": m.memory_type,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "call_count": m.call_count or 0
        } for m in memories]

        query_time = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "items": items,
            "total": len(items),
            "query_time_ms": round(query_time, 1)
        }

    def search_knowledge(self, query: str, limit: int, session: Session) -> dict:
        """搜索知识库"""
        start_time = datetime.now()

        # 搜索知识库名称和描述
        kbs = session.query(KnowledgeBase).filter(
            KnowledgeBase.name.like(f"%{query}%") |
            KnowledgeBase.description.like(f"%{query}%")
        ).limit(limit).all()

        items = []
        for kb in kbs:
            docs = session.query(Document).filter(
                Document.kb_id == kb.id,
                Document.content.like(f"%{query}%")
            ).limit(5).all()

            for doc in docs:
                items.append({
                    "id": doc.id,
                    "kb_id": kb.id,
                    "kb_name": kb.name,
                    "title": doc.filename or "文档",
                    "content": doc.content[:200] if doc.content else "",
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "view_count": doc.view_count or 0
                })

        query_time = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "items": items,
            "total": len(items),
            "query_time_ms": round(query_time, 1)
        }

    def add_search_history(self, query: str):
        """添加搜索历史"""
        session = get_session()
        try:
            cursor = session.execute(
                f"INSERT INTO search_history (query) VALUES (?)",
                (query,)
            )
            session.commit()
        finally:
            session.close()

    def get_search_history(self, limit: int = 10) -> list:
        """获取搜索历史"""
        session = get_session()
        try:
            cursor = session.execute(
                f"SELECT query, timestamp FROM search_history ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [{"query": r[0], "timestamp": r[1]} for r in rows]
        finally:
            session.close()

    def get_hot_memories(self, limit: int = 5) -> list:
        """获取热门记忆"""
        session = get_session()
        try:
            memories = session.query(Memory).order_by(
                Memory.call_count.desc()
            ).limit(limit).all()
            return [{
                "id": m.id,
                "content": m.content[:100],
                "call_count": m.call_count or 0
            } for m in memories]
        finally:
            session.close()

    def get_hot_knowledge(self, limit: int = 5) -> list:
        """获取热门知识"""
        session = get_session()
        try:
            docs = session.query(Document).order_by(
                Document.view_count.desc()
            ).limit(limit).all()
            return [{
                "id": d.id,
                "title": d.filename or "文档",
                "view_count": d.view_count or 0
            } for d in docs]
        finally:
            session.close()

    def increment_memory_call(self, memory_id: int):
        """增加记忆调用计数"""
        session = get_session()
        try:
            memory = session.query(Memory).filter(Memory.id == memory_id).first()
            if memory:
                memory.call_count = (memory.call_count or 0) + 1
                session.commit()
        finally:
            session.close()
```

- [ ] **Step 2: 提交**

```bash
git add backend/services/search_service.py
git commit -m "feat(search): add SearchService with unified_search"
```

---

### Task 3: 后端 - 搜索 API 路由

**Files:**
- Create: `backend/api/routes/search.py`
- Modify: `backend/main.py` (注册路由)

- [ ] **Step 1: 创建 search.py 路由**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.search_service import SearchService

router = APIRouter(prefix="/api/search", tags=["search"])
search_service = SearchService()

class UnifiedSearchRequest(BaseModel):
    query: str
    scopes: list = ["memory", "knowledge"]
    limit: int = 20

@router.post("/unified")
async def unified_search(req: UnifiedSearchRequest):
    if not req.query.strip():
        return {"memory": {"items": [], "total": 0}, "knowledge": {"items": [], "total": 0}}

    try:
        results = search_service.unified_search(req.query, req.scopes, req.limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_history(limit: int = 10):
    return {"history": search_service.get_search_history(limit)}

@router.get("/hot")
async def get_hot(scope: str = "memory", limit: int = 5):
    if scope == "memory":
        return {"items": search_service.get_hot_memories(limit)}
    elif scope == "knowledge":
        return {"items": search_service.get_hot_knowledge(limit)}
    else:
        return {"items": []}
```

- [ ] **Step 2: 在 main.py 中注册路由**

```python
# 在 main.py 中添加
from api.routes.search import router as search_router

app.include_router(search_router)
```

- [ ] **Step 3: 测试 API**

Run: `cd /home/wchao/workspace/Date_LIB/backend && python -c "from api.routes.search import router; print('Search routes OK')"`

- [ ] **Step 4: 提交**

```bash
git add backend/api/routes/search.py backend/main.py
git commit -m "feat(search): add unified search API routes"
```

---

### Task 4: 前端 - 搜索 Store

**Files:**
- Create: `frontend/src/stores/search.svelte.js`

- [ ] **Step 1: 创建搜索状态管理**

```javascript
let searchState = $state({
  isOpen: false,
  query: '',
  scopes: { memory: true, knowledge: true, history: false },
  results: { memory: [], knowledge: [] },
  history: [],
  hot: { memory: [], knowledge: [] },
  loading: false,
  expandedScopes: { memory: true, knowledge: true }
});

let searchDebounceTimer = null;

export function toggleSearch() {
  searchState.isOpen = !searchState.isOpen;
  if (searchState.isOpen && searchState.history.length === 0) {
    loadHistory();
    loadHot();
  }
}

export function setQuery(q) {
  searchState.query = q;
  if (debounce) {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => search(), 300);
  }
}

export function toggleScope(scope) {
  searchState.scopes[scope] = !searchState.scopes[scope];
  localStorage.setItem('searchScopes', JSON.stringify(searchState.scopes));
  if (searchState.query) search();
}

export async function search() {
  if (!searchState.query.trim()) {
    searchState.results = { memory: [], knowledge: [] };
    return;
  }

  searchState.loading = true;
  try {
    const { api } = await import('../lib/api.js');
    const activeScopes = Object.entries(searchState.scopes)
      .filter(([_, v]) => v)
      .map(([k, _]) => k);

    const resp = await api.search.unified({
      query: searchState.query,
      scopes: activeScopes,
      limit: 20
    });

    searchState.results = {
      memory: resp.data.memory?.items || [],
      knowledge: resp.data.knowledge?.items || []
    };
  } catch (e) {
    console.error('Search failed:', e);
  }
  searchState.loading = false;
}

export async function loadHistory() {
  try {
    const { api } = await import('../lib/api.js');
    const resp = await api.search.history(10);
    searchState.history = resp.data.history || [];
  } catch (e) {
    console.error('Failed to load history:', e);
  }
}

export async function loadHot() {
  try {
    const { api } = await import('../lib/api.js');
    const [memResp, kbResp] = await Promise.all([
      api.search.hot('memory', 5),
      api.search.hot('knowledge', 5)
    ]);
    searchState.hot = {
      memory: memResp.data.items || [],
      knowledge: kbResp.data.items || []
    };
  } catch (e) {
    console.error('Failed to load hot:', e);
  }
}

export { searchState };
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/stores/search.svelte.js
git commit -m "feat(search): add search state management"
```

---

### Task 5: 前端 - 搜索面板组件

**Files:**
- Create: `frontend/src/components/search/SearchPanel.svelte`
- Create: `frontend/src/components/search/SearchInput.svelte`
- Create: `frontend/src/components/search/ScopeSelector.svelte`

- [ ] **Step 1: 创建 SearchInput.svelte**

```svelte
<script>
  let { query = '', onInput } = $props();

  function handleInput(e) {
    onInput(e.target.value);
  }
</script>

<div class="relative">
  <input
    type="text"
    class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
    placeholder="搜索记忆、知识..."
    value={query}
    oninput={handleInput}
  />
  <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
</div>
```

- [ ] **Step 2: 创建 ScopeSelector.svelte**

```svelte
<script>
  let { scopes, onToggle } = $props();

  const scopeLabels = {
    memory: '记忆',
    knowledge: '知识',
    history: '历史'
  };
</script>

<div class="flex gap-4">
  {#each Object.entries(scopeLabels) as [key, label]}
    <label class="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={scopes[key]}
        onchange={() => onToggle(key)}
        class="w-4 h-4 rounded border-gray-300 text-blue-500"
      />
      <span class="text-sm text-gray-700">{label}</span>
    </label>
  {/each}
</div>
```

- [ ] **Step 3: 创建 SearchPanel.svelte**

```svelte
<script>
  import { searchState, toggleSearch, setQuery, toggleScope, search, loadHistory, loadHot } from '../../stores/search.svelte.js';
  import SearchInput from './SearchInput.svelte';
  import ScopeSelector from './ScopeSelector.svelte';
  import SearchResults from './SearchResults.svelte';
  import SearchHistory from './SearchHistory.svelte';
  import HotItems from './HotItems.svelte';

  function handleInput(q) {
    setQuery(q);
    if (q.trim()) search();
  }

  function handleToggleScope(scope) {
    toggleScope(scope);
  }

  function handleHistoryClick(query) {
    setQuery(query);
    search();
  }
</script>

{#if searchState.isOpen}
<div class="w-96 h-full bg-white border-l border-gray-200 shadow-lg flex flex-col">
  <!-- Header -->
  <div class="p-4 border-b border-gray-100">
    <div class="flex items-center justify-between mb-4">
      <h3 class="font-semibold text-gray-800">搜索</h3>
      <button class="text-gray-400 hover:text-gray-600" onclick={toggleSearch}>×</button>
    </div>
    <SearchInput query={searchState.query} onInput={handleInput} />
    <div class="mt-3">
      <ScopeSelector scopes={searchState.scopes} onToggle={handleToggleScope} />
    </div>
  </div>

  <!-- Content -->
  <div class="flex-1 overflow-auto p-4">
    {#if searchState.loading}
      <div class="text-center py-8 text-gray-500">搜索中...</div>
    {:else if searchState.query && (searchState.results.memory.length > 0 || searchState.results.knowledge.length > 0)}
      <SearchResults results={searchState.results} />
    {:else if searchState.query}
      <div class="text-center py-8 text-gray-400">未找到结果</div>
    {:else}
      <SearchHistory items={searchState.history} onSelect={handleHistoryClick} />
      <div class="mt-6">
        <HotItems items={searchState.hot} />
      </div>
    {/if}
  </div>
</div>
{/if}
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/search/SearchPanel.svelte frontend/src/components/search/SearchInput.svelte frontend/src/components/search/ScopeSelector.svelte
git commit -m "feat(search): add search panel components"
```

---

### Task 6: 前端 - 搜索结果组件

**Files:**
- Create: `frontend/src/components/search/SearchResults.svelte`
- Create: `frontend/src/components/search/SearchHistory.svelte`
- Create: `frontend/src/components/search/HotItems.svelte`

- [ ] **Step 1: 创建 SearchResults.svelte**

```svelte
<script>
  let { results } = $props();

  function formatTime(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    const hours = diff / (1000 * 60 * 60);
    if (hours < 1) return '刚刚';
    if (hours < 24) return `${Math.floor(hours)}小时前`;
    const days = hours / 24;
    if (days < 7) return `${Math.floor(days)}天前`;
    return date.toLocaleDateString();
  }
</script>

<div class="space-y-6">
  <!-- Memory Results -->
  {#if results.memory && results.memory.length > 0}
    <div>
      <h4 class="text-sm font-medium text-gray-500 mb-3 flex items-center gap-2">
        🧠 记忆库 ({results.memory.length})
      </h4>
      <div class="space-y-2">
        {#each results.memory as item}
          <div class="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors">
            <div class="flex justify-between items-start mb-1">
              <span class="badge badge-info">{item.memory_type}</span>
              <span class="text-xs text-gray-400">{formatTime(item.created_at)}</span>
            </div>
            <p class="text-sm text-gray-700 line-clamp-2">{item.content}</p>
            {#if item.call_count > 0}
              <div class="text-xs text-gray-400 mt-1">调用 {item.call_count} 次</div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Knowledge Results -->
  {#if results.knowledge && results.knowledge.length > 0}
    <div>
      <h4 class="text-sm font-medium text-gray-500 mb-3 flex items-center gap-2">
        📚 知识库 ({results.knowledge.length})
      </h4>
      <div class="space-y-2">
        {#each results.knowledge as item}
          <div class="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors">
            <div class="flex justify-between items-start mb-1">
              <span class="font-medium text-gray-800">{item.title}</span>
              <span class="text-xs text-gray-400">{formatTime(item.created_at)}</span>
            </div>
            <p class="text-sm text-gray-600">{item.kb_name}</p>
            <p class="text-xs text-gray-400 mt-1 line-clamp-1">{item.content}</p>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>
```

- [ ] **Step 2: 创建 SearchHistory.svelte**

```svelte
<script>
  let { items = [], onSelect } = $props();

  function formatTime(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    const hours = diff / (1000 * 60 * 60);
    if (hours < 1) return '刚刚';
    if (hours < 24) return `${Math.floor(hours)}小时前`;
    const days = hours / 24;
    if (days < 7) return `${Math.floor(days)}天前`;
    return date.toLocaleDateString();
  }
</script>

{#if items.length > 0}
<div>
  <div class="flex items-center justify-between mb-3">
    <h4 class="text-sm font-medium text-gray-500">搜索历史</h4>
    <button class="text-xs text-blue-500 hover:underline">清除</button>
  </div>
  <div class="space-y-1">
    {#each items as item}
      <button
        class="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg flex justify-between items-center"
        onclick={() => onSelect(item.query)}
      >
        <span>🔍 {item.query}</span>
        <span class="text-xs text-gray-400">{formatTime(item.timestamp)}</span>
      </button>
    {/each}
  </div>
</div>
{/if}
```

- [ ] **Step 3: 创建 HotItems.svelte**

```svelte
<script>
  let { items = { memory: [], knowledge: [] } } = $props();
</script>

<div class="space-y-4">
  {#if items.memory && items.memory.length > 0}
    <div>
      <h4 class="text-sm font-medium text-gray-500 mb-2">🔥 热门记忆</h4>
      <div class="space-y-1">
        {#each items.memory as item}
          <div class="px-3 py-2 text-sm text-gray-700 flex justify-between items-center bg-orange-50 rounded">
            <span class="truncate flex-1">{item.content}</span>
            <span class="text-xs text-orange-600 ml-2">{item.call_count}次</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  {#if items.knowledge && items.knowledge.length > 0}
    <div>
      <h4 class="text-sm font-medium text-gray-500 mb-2">📖 热门知识</h4>
      <div class="space-y-1">
        {#each items.knowledge as item}
          <div class="px-3 py-2 text-sm text-gray-700 flex justify-between items-center bg-blue-50 rounded">
            <span class="truncate flex-1">{item.title}</span>
            <span class="text-xs text-blue-600 ml-2">{item.view_count}次</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/search/SearchResults.svelte frontend/src/components/search/SearchHistory.svelte frontend/src/components/search/HotItems.svelte
git commit -m "feat(search): add search results and history components"
```

---

### Task 7: 前端 - 集成到侧边栏

**Files:**
- Modify: `frontend/src/components/Sidebar.svelte`
- Modify: `frontend/src/lib/api.js`

- [ ] **Step 1: 在 api.js 中添加搜索 API**

```javascript
export const api = {
  // ... existing APIs ...

  search: {
    unified: (data) => getApi().post('/api/search/unified', data),
    history: (limit) => getApi().get('/api/search/history', { params: { limit } }),
    hot: (scope, limit) => getApi().get('/api/search/hot', { params: { scope, limit } }),
  },
};
```

- [ ] **Step 2: 修改 Sidebar.svelte 添加搜索按钮**

```svelte
<script>
  import { appState } from '../stores/app.svelte.js';
  import { toggleSearch } from '../stores/search.svelte.js';

  const tabs = [
    { id: 'startup', label: '启动引导', icon: '⚡' },
    { id: 'knowledge', label: '知识库', icon: '📚' },
    { id: 'memory', label: '记忆库', icon: '🧠' },
    { id: 'import', label: '对话导入', icon: '📥' },
    { id: 'channel', label: '通道路由', icon: '🔀' },
    { id: 'settings', label: '设置', icon: '⚙️' },
  ];
</script>

<nav class="w-56 h-full bg-white border-r border-gray-200 flex flex-col shadow-sm">
  <!-- Search Toggle -->
  <div class="p-3 border-b border-gray-100">
    <button
      class="w-full flex items-center gap-2 px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
      onclick={toggleSearch}
    >
      <span>🔍</span>
      <span class="text-sm">搜索</span>
    </button>
  </div>

  <!-- Tabs -->
  <ul class="flex-1 py-2">
    {#each tabs as tab}
      <li>
        <button
          class="w-full px-4 py-3 text-left flex items-center gap-3 transition-colors {appState.currentTab === tab.id ? 'bg-blue-50 text-blue-600 border-r-2 border-blue-500' : 'text-gray-600 hover:bg-gray-50'}"
          onclick={() => appState.currentTab = tab.id}
        >
          <span>{tab.icon}</span>
          <span class="font-medium">{tab.label}</span>
        </button>
      </li>
    {/each}
  </ul>

  <!-- Footer -->
  <div class="p-4 border-t border-gray-100 text-xs text-gray-400">
    v0.1.0 · Phase 2
  </div>
</nav>
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/Sidebar.svelte frontend/src/lib/api.js
git commit -m "feat(search): integrate search panel into sidebar"
```

---

### Task 8: 集成测试

**Files:**
- 测试所有组件

- [ ] **Step 1: 运行前端构建**

Run: `cd /home/wchao/workspace/Date_LIB/frontend && npm run build`

- [ ] **Step 2: 验证后端 API**

Run: `cd /home/wchao/workspace/Date_LIB/backend && python -c "
from api.routes.search import router
print('API routes OK')
from services.search_service import SearchService
s = SearchService()
print('SearchService OK')
"`

- [ ] **Step 3: 提交所有更改**

```bash
git add -A
git commit -m "feat: implement unified search center

- Add SearchService with unified search across memory and knowledge
- Add search API routes (/api/search/unified, /history, /hot)
- Add frontend SearchPanel with scope selector
- Add search results, history, and hot items components
- Integrate search panel into sidebar"
```

---

## 验证清单

- [ ] 搜索输入 → 结果 500ms 内显示
- [ ] 选择不同范围 → 结果正确过滤
- [ ] 搜索历史 → 显示最近 10 条
- [ ] 热门推荐 → 显示调用次数最高的记忆/知识
- [ ] 前端构建成功
- [ ] 后端 API 导入无错误

---

## 备选实施顺序

如果 Task 3（API 路由）太早有问题，可以先完成 Task 1-2，然后测试服务层，再继续。

**Plan complete and saved to `docs/superpowers/plans/2026-04-30-unified-search-impl.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
