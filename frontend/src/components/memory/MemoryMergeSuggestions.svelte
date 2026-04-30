<script>
  import { api } from '../../lib/api.js';
  import { addToast } from '../../stores/toast.svelte.js';

  let { similarMemories, onMerge } = $props();

  let selectedIds = $state([]);
  let mergedContent = $state('');
  let mergedType = $state('');
  let merging = $state(false);
  let error = $state('');
  let showMergeEditor = $state(false);

  const memoryTypes = [
    { id: 'preference', label: '偏好习惯' },
    { id: 'expertise', label: '专业知识' },
    { id: 'project_context', label: '项目上下文' },
  ];

  function toggleSelection(memoryId) {
    if (selectedIds.includes(memoryId)) {
      selectedIds = selectedIds.filter(id => id !== memoryId);
    } else {
      selectedIds = [...selectedIds, memoryId];
    }
  }

  function selectAll() {
    selectedIds = similarMemories.map(m => m.memory_id);
  }

  function clearSelection() {
    selectedIds = [];
  }

  function openMergeEditor() {
    if (selectedIds.length < 2) {
      error = '至少需要选择 2 条记忆才能合并';
      return;
    }

    // 获取选中的记忆
    const selectedMemories = similarMemories.filter(m => selectedIds.includes(m.memory_id));

    // 默认使用第一条记忆的类型
    mergedType = selectedMemories[0].type;

    // 默认合并内容为所有选中记忆的内容拼接
    mergedContent = selectedMemories.map(m => m.content).join('\n\n');

    error = '';
    showMergeEditor = true;
  }

  function closeMergeEditor() {
    showMergeEditor = false;
    mergedContent = '';
    mergedType = '';
    error = '';
  }

  async function handleMerge() {
    if (!mergedContent.trim()) {
      error = '合并后的内容不能为空';
      return;
    }

    merging = true;
    error = '';

    try {
      const response = await api.memory.merge(selectedIds, mergedContent, mergedType);

      addToast(`合并成功：${response.data.merged_memory_id}`, 'success');

      if (onMerge) {
        onMerge(response.data);
      }

      closeMergeEditor();
      clearSelection();
    } catch (e) {
      error = '合并失败：' + e.message;
      addToast('合并失败：' + e.message, 'error');
    } finally {
      merging = false;
    }
  }

  function handleKeydown(e) {
    if (e.key === 'Escape' && showMergeEditor) {
      closeMergeEditor();
    }
  }
</script>

<div class="bg-white rounded-lg shadow p-4">
  <div class="flex justify-between items-center mb-4">
    <h2 class="font-semibold">相似记忆合并</h2>
    <div class="flex gap-2">
      <button
        class="text-xs px-2 py-1 bg-gray-200 rounded hover:bg-gray-300"
        onclick={selectAll}
      >
        全选
      </button>
      <button
        class="text-xs px-2 py-1 bg-gray-200 rounded hover:bg-gray-300"
        onclick={clearSelection}
      >
        清除
      </button>
    </div>
  </div>

  {#if error}
    <div class="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
      {error}
    </div>
  {/if}

  {#if similarMemories.length === 0}
    <div class="text-center py-8 text-gray-400">
      <p>暂无相似记忆</p>
    </div>
  {:else}
    <div class="space-y-3 max-h-96 overflow-y-auto">
      {#each similarMemories as memory}
        <div class="p-3 bg-gray-50 rounded-lg border-2 transition-colors" class:border-blue-500={selectedIds.includes(memory.memory_id)}>
          <div class="flex items-start gap-3">
            <input
              type="checkbox"
              class="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              checked={selectedIds.includes(memory.memory_id)}
              onchange={() => toggleSelection(memory.memory_id)}
            />
            <div class="flex-1">
              <div class="flex justify-between items-start mb-2">
                <span class="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                  {memory.type}
                </span>
                <span class="text-xs text-gray-400">
                  置信度：{Math.round(memory.confidence * 100)}%
                </span>
              </div>
              <div class="text-sm">{memory.content}</div>
              <div class="mt-2 text-xs text-gray-400">
                {new Date(memory.created_at).toLocaleString('zh-CN')}
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>

    <!-- 合并按钮 -->
    <div class="mt-4 flex justify-between items-center">
      <span class="text-sm text-gray-600">
        已选择 {selectedIds.length} 条记忆
      </span>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        onclick={openMergeEditor}
        disabled={selectedIds.length < 2}
      >
        合并选中的记忆
      </button>
    </div>
  {/if}

  <!-- 合并编辑弹窗 -->
  {#if showMergeEditor}
    <div
      class="fixed inset-0 bg-black bg-opacity-50 z-40 flex items-center justify-center p-4"
      onclick={closeMergeEditor}
      onkeydown={handleKeydown}
      role="dialog"
      aria-modal="true"
    >
      <div
        class="bg-white rounded-lg shadow-xl w-full max-w-lg z-50"
        onclick={(e) => e.stopPropagation()}
      >
        <!-- 标题栏 -->
        <div class="flex justify-between items-center p-4 border-b">
          <h2 class="text-lg font-semibold">确认合并内容</h2>
          <button
            class="text-gray-400 hover:text-gray-600 text-xl"
            onclick={closeMergeEditor}
            aria-label="关闭"
          >
            &times;
          </button>
        </div>

        <!-- 内容区域 -->
        <div class="p-4 space-y-4">
          <!-- 类型选择 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              合并后的类型
            </label>
            <select
              class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              bind:value={mergedType}
            >
              {#each memoryTypes as type}
                <option value={type.id}>{type.label}</option>
              {/each}
            </select>
          </div>

          <!-- 内容编辑 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              合并后的内容
            </label>
            <textarea
              class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-h-[200px]"
              bind:value={mergedContent}
              placeholder="编辑合并后的内容..."
            ></textarea>
            <p class="text-xs text-gray-500 mt-1">提示：可以编辑合并后的内容</p>
          </div>
        </div>

        <!-- 按钮区域 -->
        <div class="flex justify-end gap-3 p-4 border-t bg-gray-50 rounded-b-lg">
          <button
            class="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            onclick={closeMergeEditor}
            disabled={merging}
          >
            取消
          </button>
          <button
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            onclick={handleMerge}
            disabled={merging}
          >
            {merging ? '合并中...' : '确认合并'}
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>
