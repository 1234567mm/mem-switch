# 记忆管理增强设计文档

## 概述

增强 Mem-Switch 的记忆管理能力，新增编辑、合并、失效/过期、使用统计功能。

## 功能清单

### 1. 记忆编辑 + 删除

**编辑功能**：
- 修改记忆内容
- 修改记忆类型（偏好习惯 / 专业知识 / 项目上下文）
- 修改维度数据（dimensions）

**删除功能**：
- 单个删除
- 批量删除
- 删除确认对话框

**API**：
```
PATCH /api/memory/{id}
Body: { "content": "string", "memory_type": "string", "dimensions": {} }

DELETE /api/memory/{id}
DELETE /api/memory/batch  # 批量删除
Body: { "ids": ["id1", "id2"] }
```

### 2. 记忆合并（AI 智能建议）

**触发时机**：
- 用户点击"检查合并建议"按钮
- 或定时任务（可选）

**合并建议流程**：
1. 系统搜索相似记忆（向量相似度 > 0.85）
2. 按内容聚类分组
3. 使用 LLM 分析每组，生成合并建议
4. 返回可合并的记忆组及建议

**合并执行**：
- 用户确认后执行
- 保留 `confidence` 最高的记忆
- 更新内容的 `source_session_id` 为 "merged"

**API**：
```
POST /api/memory/suggest-merge
Response: {
  "suggestions": [
    {
      "group_id": "xxx",
      "memories": [...],
      "suggested_content": "合并后的内容",
      "reason": "两条记忆内容相似..."
    }
  ]
}

POST /api/memory/merge
Body: { "group_id": "xxx", "keep_id": "memory_id_to_keep" }
```

### 3. 记忆失效/过期

**手动标记失效**：
- 用户点击"失效"按钮
- 记忆标记为 `invalidated: true`
- 不参与搜索和注入

**恢复失效记忆**：
- 用户可点击"恢复"按钮
- 撤销失效标记

**自动过期**：
- 记忆创建时记录 `expires_at`
- 默认 180 天（可配置）
- 后台任务定期清理过期记忆

**API**：
```
POST /api/memory/{id}/invalidate
Body: { "invalidate": true }

POST /api/memory/check-expiry  # 后台调用
Response: { "expired_count": 5 }
```

### 4. 记忆使用统计

**追踪指标**：
- `call_count`: 被注入到 prompt 的次数
- `last_called_at`: 最后调用时间

**更新时机**：
- 每次 `MemoryInjector.inject()` 被调用时

**前端展示**：
- 记忆卡片显示调用次数
- 记忆详情页显示完整统计

**API**：
```
GET /api/memory/{id}/stats
Response: { "call_count": 15, "last_called_at": "2026-04-30T10:00:00Z" }
```

## 数据库变更

### Vector Store 扩展

Chroma `memories` collection 增加字段：
- `invalidated`: bool (default false)
- `expires_at`: datetime (nullable)
- `call_count`: int (default 0)
- `last_called_at`: datetime (nullable)

## 后端服务变更

### MemoryService 扩展

```python
class MemoryService:
    # 新增方法
    def update_memory(self, memory_id, content, memory_type, dimensions):
        """更新记忆"""

    def delete_memory(self, memory_id):
        """删除记忆"""

    def batch_delete_memories(self, memory_ids):
        """批量删除"""

    def invalidate_memory(self, memory_id, invalidate=True):
        """标记失效/恢复"""

    def suggest_merges(self) -> list:
        """AI 合并建议"""

    def merge_memories(self, group_id, keep_id):
        """执行合并"""

    def increment_call_count(self, memory_id):
        """增加调用计数"""

    def check_expiry(self) -> int:
        """检查过期，返回过期数量"""
```

### MemoryInjector 修改

在 `inject()` 方法中，更新 `call_count` 和 `last_called_at`。

## 前端组件

### MemoryView 增强

```
- 记忆列表添加"编辑"和"失效"按钮
- 记忆卡片显示 call_count
- 添加"检查合并建议"按钮
- 添加批量选择删除功能
```

### MemoryEditModal

```
- 记忆内容编辑框
- 类型选择下拉
- 维度数据编辑（可选）
- 保存/取消按钮
```

### MemoryMergeSuggestions

```
- 合并建议列表
- 每组显示涉及的記憶
- 预览合并后内容
- 确认/拒绝按钮
```

## 实施顺序

1. **Phase 1**: 数据库/服务层 - 新增字段和基础 API
2. **Phase 2**: 前端 - 记忆列表编辑/删除/失效按钮
3. **Phase 3**: 前端 - 合并建议功能
4. **Phase 4**: 集成测试

## 验证方式

1. 创建记忆 → 编辑 → 保存成功
2. 创建多个相似记忆 → 检查合并建议
3. 标记记忆失效 → 搜索不到该记忆
4. 调用记忆注入 → call_count 增加
