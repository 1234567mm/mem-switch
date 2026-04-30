# 统一搜索中心设计文档

## 概述

统一搜索中心为 Mem-Switch 提供跨记忆库、知识库、对话历史的全局搜索能力。用户可自定义搜索范围，结果分类展示，支持搜索历史和热门推荐。

## 用户场景

1. 用户想快速找到之前导入的某个主题的记忆
2. 用户想在知识库和记忆中同时搜索某个概念
3. 用户想查看最近搜索历史快速重复搜索
4. 用户想发现热门/常用的记忆和知识

## 设计决策

### 搜索入口
- 位置：侧边栏顶部
- 形式：可展开的搜索输入框
- 默认展开状态：折叠（点击展开）

### 搜索范围选择
- 选项：记忆库、知识库、对话历史
- 用户勾选后记住选择（localStorage）
- 默认勾选：记忆库 + 知识库

### 结果展示
- 按类别分组展示（分类卡片）
- 每组内按时间倒序
- 相似内容聚合显示
- 支持展开查看详情

### 性能策略
- 小数据量（< 1000 条）：直接全文搜索
- 大数据量（>= 1000 条）：向量嵌入搜索
- 防抖：300ms
- 异步加载，渐进展示

## 前端设计

### 组件结构

```
SearchPanel (搜索面板 - 侧边栏顶部)
├── SearchInput (搜索输入框)
├── ScopeSelector (搜索范围选择器)
├── SearchHistory (搜索历史)
├── HotItems (热门推荐)
└── SearchResults (搜索结果)
    ├── MemoryResults (记忆结果卡片)
    ├── KnowledgeResults (知识结果卡片)
    └── HistoryResults (历史结果卡片)
```

### 文件结构

```
frontend/src/
├── components/
│   ├── search/
│   │   ├── SearchPanel.svelte      # 主搜索面板
│   │   ├── SearchInput.svelte      # 搜索输入框
│   │   ├── ScopeSelector.svelte    # 范围选择器
│   │   ├── SearchResults.svelte     # 结果展示
│   │   ├── SearchHistory.svelte     # 搜索历史
│   │   └── HotItems.svelte         # 热门推荐
│   └── shared/
│       └── Toast.svelte            # 复用已存在
├── stores/
│   └── search.svelte.js            # 搜索状态管理
└── lib/
    └── api.js                       # 扩展搜索API
```

### UI 布局

**侧边栏顶部区域**：
```
┌────────────────────────────┐
│ 🔍 搜索记忆、知识...         │
├────────────────────────────┤
│ ☐ 记忆  ☐ 知识  ☐ 历史      │
└────────────────────────────┘
```

**展开后搜索结果面板**：
```
┌─────────────────────────────────────────┐
│ 搜索: [________________________] 🔍     │
├─────────────────────────────────────────┤
│ 搜索历史                    最近清除     │
│ ├─ Python 异步编程        1小时前        │
│ ├─ React 状态管理          昨天         │
│ └─ 数据库优化              3天前         │
├─────────────────────────────────────────┤
│ 热门推荐                                │
│ ├─ 🧠 项目配置记忆 (调用 23次)          │
│ └─ 📚 API 设计规范 (查看 45次)          │
├─────────────────────────────────────────┤
│ 🧠 记忆库 (3)                 更多 >     │
│ ┌─────────────────────────────────────┐ │
│ │ [记忆标题] · 2小时前                  │ │
│ │ 记忆内容摘要...                       │ │
│ │ 相似记忆: 2 条                        │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ [记忆标题] · 昨天                     │ │
│ └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│ 📚 知识库 (2)                 更多 >     │
│ ...                                     │
└─────────────────────────────────────────┘
```

## 后端设计

### 新增 API

#### 1. 统一搜索接口

```
POST /api/search/unified
```

Request:
```json
{
  "query": "搜索关键词",
  "scopes": ["memory", "knowledge"],
  "limit": 20
}
```

Response:
```json
{
  "memory": {
    "items": [
      {
        "id": "mem_xxx",
        "content": "记忆内容",
        "memory_type": "preference",
        "created_at": "2026-04-30T10:00:00Z",
        "similar_count": 2
      }
    ],
    "total": 100,
    "query_time_ms": 45
  },
  "knowledge": {
    "items": [...],
    "total": 50,
    "query_time_ms": 120
  }
}
```

#### 2. 搜索历史接口

```
GET /api/search/history?limit=10
```

Response:
```json
{
  "history": [
    {"query": "Python 异步编程", "timestamp": "2026-04-30T09:00:00Z"},
    {"query": "React 状态管理", "timestamp": "2026-04-29T10:00:00Z"}
  ]
}
```

#### 3. 热门内容接口

```
GET /api/search/hot?scope=memory&limit=5
GET /api/search/hot?scope=knowledge&limit=5
```

Response:
```json
{
  "memory": [
    {"id": "mem_xxx", "content": "...", "call_count": 23}
  ],
  "knowledge": [
    {"id": "kb_xxx", "title": "...", "view_count": 45}
  ]
}
```

### 服务层扩展

**新增 SearchService** (`backend/services/search_service.py`):
- `unified_search(query, scopes, limit)` - 统一搜索
- `get_search_history(limit)` - 获取搜索历史
- `get_hot_items(scope, limit)` - 获取热门内容
- `add_search_history(query)` - 添加搜索历史
- `increment_call_count(item_id, scope)` - 增加调用计数

**数据存储**:
- 搜索历史：SQLite 表 `search_history`
- 热门计数：复用现有 memories 表增加 `call_count` 字段
- 知识库查看次数：documents 表增加 `view_count` 字段

## 数据库变更

### 新增表

```sql
CREATE TABLE search_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  query TEXT NOT NULL,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_search_history_timestamp ON search_history(timestamp DESC);
```

### 表结构扩展

```sql
-- memories 表增加调用计数
ALTER TABLE memories ADD COLUMN call_count INTEGER DEFAULT 0;

-- documents 表增加查看计数
ALTER TABLE documents ADD COLUMN view_count INTEGER DEFAULT 0;
```

## 性能优化

### 小数据量优化 (< 1000 条)
- 直接 SQL LIKE 搜索
- 目标响应时间：< 100ms

### 大数据量优化 (>= 1000 条)
- 向量嵌入搜索（使用 Ollama embed）
- ChromaDB similarity search
- 结果缓存（5分钟 TTL）
- 分页加载
- 目标响应时间：< 500ms

### 前端优化
- 搜索防抖：300ms
- 结果骨架屏加载
- 滚动加载更多

## 实施顺序

1. **Phase 1**: 后端 - 统一搜索 API + 搜索历史
2. **Phase 2**: 前端 - 搜索面板组件
3. **Phase 3**: 前端 - 结果展示 + 热门推荐
4. **Phase 4**: 集成测试 + 性能优化

## 验证方式

1. 搜索输入 → 结果 500ms 内显示
2. 选择不同范围 → 结果正确过滤
3. 搜索历史 → 显示最近 10 条
4. 热门推荐 → 显示调用次数最高的记忆
5. 点击记忆 → 跳转详情页面
