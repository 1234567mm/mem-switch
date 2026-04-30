<script>
  import { api } from '../lib/api.js';
  import { addToast } from '../stores/toast.svelte.js';
  import MemoryEditModal from './memory/MemoryEditModal.svelte';

  let memories = $state([]);
  let searchQuery = $state('');
  let searchResults = $state([]);
  let selectedType = $state('');
  let loading = $state(false);
  let error = $state('');

  // 编辑弹窗相关
  let editingMemory = $state(null);
  let showEditModal = $state(false);

  // 统计信息缓存
  let statsCache = $state({});

  const memoryTypes = [
    { id: '', label: '全部' },
    { id: 'preference', label: '偏好习惯' },
    { id: 'expertise', label: '专业知识' },
    { id: 'project_context', label: '项目上下文' },
  ];

  async function loadMemories() {
    loading = true;
    error = '';
    try {
      const resp = await api.memory.list(selectedType || null);
      memories = resp.data;
      // 为每个记忆加载统计信息
      memories.forEach(m => loadStats(m.memory_id));
    } catch (e) {
      error = '加载记忆失败：' + e.message;
    }
    loading = false;
  }

  async function searchMemories() {
    if (!searchQuery.trim()) return;
    loading = true;
    try {
      const resp = await api.memory.search(searchQuery, selectedType || null, 20);
      searchResults = resp.data;
    } catch (e) {
      error = '搜索失败：' + e.message;
    }
    loading = false;
  }

  async function deleteMemory(memoryId) {
    if (!confirm('确定删除这条记忆吗？')) return;
    try {
      await api.memory.delete(memoryId);
      addToast('记忆删除成功', 'success');
      await loadMemories();
    } catch (e) {
      error = '删除失败：' + e.message;
      addToast('删除失败：' + e.message, 'error');
    }
  }

  async function invalidateMemory(memoryId, currentInvalidated) {
    const action = currentInvalidated ? '恢复' : '失效';
    try {
      await api.memory.invalidate(memoryId, !currentInvalidated);
      addToast(`记忆已${action}`, 'success');
      await loadMemories();
    } catch (e) {
      addToast(`${action}失败：` + e.message, 'error');
    }
  }

  function openEditModal(memory) {
    editingMemory = memory;
    showEditModal = true;
  }

  function closeEditModal() {
    showEditModal = false;
    editingMemory = null;
  }

  async function handleMemoryUpdate() {
    await loadMemories();
    closeEditModal();
  }

  async function loadStats(memoryId) {
    try {
      const resp = await api.memory.getStats(memoryId);
      statsCache[memoryId] = resp.data;
    } catch (e) {
      // 静默失败，不显示错误
    }
  }

  function formatDate(dateStr) {
    try {
      return new Date(dateStr).toLocaleString('zh-CN');
    } catch {
      return dateStr;
    }
  }

  function getTypeLabel(type) {
    const found = memoryTypes.find(t => t.id === type);
    return found ? found.label : type;
  }

  $effect(() => {
    loadMemories();
  });

  $effect(() => {
    // 当选择类型变化时重新加载
    selectedType;
    loadMemories();
  });
</script>

<div class="max-w-6xl mx-auto p-6">
  <div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold">记忆库</h1>
  </div>

  {#if error}
    <div class="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">{error}</div>
  {/if}

  <!-- 编辑弹窗 -->
  {#if showEditModal && editingMemory}
    <MemoryEditModal
      memory={editingMemory}
      onClose={closeEditModal}
      onUpdate={handleMemoryUpdate}
    />
  {/if}

  <div class="grid grid-cols-2 gap-6">
    <!-- 左侧：记忆列表 -->
    <div class="bg-white rounded-lg shadow p-4">
      <div class="flex justify-between items-center mb-4">
        <h2 class="font-semibold">记忆列表</h2>
        <select
          class="border rounded-lg px-3 py-1 text-sm"
          bind:value={selectedType}
        >
          {#each memoryTypes as type}
            <option value={type.id}>{type.label}</option>
          {/each}
        </select>
      </div>

      {#if loading && memories.length === 0}
        <p class="text-gray-500">加载中...</p>
      {:else if memories.length === 0}
        <div class="text-center py-8 text-gray-400">
          <p>暂无记忆</p>
          <p class="text-sm mt-2">从对话导入中提取的记忆将显示在这里</p>
        </div>
      {:else}
        <div class="space-y-3 max-h-96 overflow-y-auto">
          {#each memories as memory}
            <div class="p-3 bg-gray-50 rounded-lg">
              <div class="flex justify-between items-start mb-2">
                <span class="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                  {getTypeLabel(memory.type)}
                </span>
                {#if memory.invalidated}
                  <span class="text-xs px-2 py-1 bg-yellow-100 text-yellow-700 rounded">
                    已失效
                  </span>
                {/if}
              </div>
              <div class="mt-2 text-sm">{memory.content}</div>

              <!-- 统计信息 -->
              {#if statsCache[memory.memory_id]}
                <div class="mt-2 flex gap-3 text-xs">
                  <span class="text-gray-500">
                    调用：{statsCache[memory.memory_id].call_count} 次
                  </span>
                  {#if statsCache[memory.memory_id].last_called_at}
                    <span class="text-gray-500">
                      最后：{formatDate(statsCache[memory.memory_id].last_called_at)}
                    </span>
                  {/if}
                </div>
              {:else}
                <div class="mt-2 text-xs text-gray-400">加载中...</div>
              {/if}

              <!-- 操作按钮 -->
              <div class="mt-3 flex gap-2 flex-wrap">
                <button
                  class="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                  onclick={() => openEditModal(memory)}
                >
                  编辑
                </button>
                <button
                  class="text-xs px-2 py-1 rounded hover:opacity-80"
                  class:bg-yellow-600={!memory.invalidated}
                  class:bg-green-600={memory.invalidated}
                  class:text-white={true}
                  onclick={() => invalidateMemory(memory.memory_id, !!memory.invalidated)}
                >
                  {memory.invalidated ? '恢复' : '失效'}
                </button>
                <button
                  class="text-xs px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                  onclick={() => deleteMemory(memory.memory_id)}
                >
                  删除
                </button>
              </div>

              <div class="mt-2 text-xs text-gray-400">
                {formatDate(memory.created_at)}
                {#if memory.source_session_id}
                  · 来源：{memory.source_session_id.slice(0, 8)}...
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <!-- 右侧：记忆搜索 -->
    <div class="bg-white rounded-lg shadow p-4">
      <h2 class="font-semibold mb-4">记忆检索</h2>

      <div class="flex gap-2 mb-4">
        <input
          type="text"
          class="flex-1 border rounded-lg px-3 py-2"
          placeholder="输入关键词搜索记忆..."
          bind:value={searchQuery}
          onkeydown={(e) => e.key === 'Enter' && searchMemories()}
        />
        <button
          class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          onclick={searchMemories}
          disabled={loading}
        >
          {loading ? '搜索中...' : '搜索'}
        </button>
      </div>

      {#if searchResults.length > 0}
        <div class="space-y-3 max-h-96 overflow-y-auto">
          {#each searchResults as result}
            <div class="p-3 bg-gray-50 rounded-lg">
              <div class="flex justify-between items-start">
                <span class="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">
                  {getTypeLabel(result.type)}
                </span>
                <span class="text-xs text-gray-400">
                  {Math.round(result.confidence * 100)}% 置信度
                </span>
              </div>
              <div class="mt-2 text-sm">{result.content}</div>
              <div class="mt-2 text-xs text-gray-400">
                {formatDate(result.created_at)}
              </div>
            </div>
          {/each}
        </div>
      {:else if searchQuery && !loading}
        <div class="text-center py-8 text-gray-400">
          <p>无搜索结果</p>
        </div>
      {:else}
        <div class="text-center py-8 text-gray-400">
          <p>输入关键词搜索记忆</p>
        </div>
      {/if}
    </div>
  </div>

  <!-- 统计信息 -->
  <div class="mt-6 bg-white rounded-lg shadow p-4">
    <h2 class="font-semibold mb-3">记忆统计</h2>
    <div class="grid grid-cols-3 gap-4">
      {#each memoryTypes.slice(1) as type}
        {@const count = memories.filter(m => m.type === type.id).length}
        <div class="text-center p-3 bg-gray-50 rounded-lg">
          <div class="text-2xl font-bold text-blue-600">{count}</div>
          <div class="text-sm text-gray-500">{type.label}</div>
        </div>
      {/each}
    </div>
  </div>
</div>
